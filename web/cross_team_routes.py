from typing import Any

import httpx
from fastapi import APIRouter, Query, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from tests.http_cross_tester import is_self_target, run_cross_team_tests
from web.cross_team_storage import cross_store

try:
    import coverage
    _HAS_COVERAGE = True
except ImportError:
    _HAS_COVERAGE = False

_system_coverage_instances: dict[str, Any] = {}

system_router = APIRouter(tags=["Cross-Team System Interface"])
tester_router = APIRouter(tags=["Cross-Team Tester Interface"])


# --- Schemas ---

class SystemSetupRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="Unique session identifier for the test run")
    setup: dict[str, Any] = Field(default_factory=dict, description="Initial setup parameters")


class TesterSetupRequest(BaseModel):
    target_url: str = Field(
        ...,
        min_length=1,
        json_schema_extra={"format": "uri"},
        description="Base URL of the target system under test",
    )


class TesterRunRequest(BaseModel):
    session_id: str = Field(
        ...,
        min_length=1,
        description="Unique session identifier generated during tester setup",
    )


# --- System Role Endpoints ---

@system_router.post("/test/setup", status_code=201)
async def system_setup(req: SystemSetupRequest):
    """Initializes session resources on the target system (docs/student-facing-spec.md)."""
    try:
        cross_store.register_system_session(req.session_id, req.setup)
        if _HAS_COVERAGE:
            try:
                # Session-scoped coverage tracer measuring core/ and web/ modules
                cov = coverage.Coverage(
                    source=["core", "web"],
                    omit=["tests/*", "web/cross_team_*"],
                )
                cov.start()
                _system_coverage_instances[req.session_id] = cov
            except Exception:
                pass
        return JSONResponse(
            status_code=201,
            content={"session_id": req.session_id},
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=409,
            content={"message": str(exc), "source": "system"},
        )
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=500,
            content={"message": f"System preparation failed: {exc}", "source": "system"},
        )


@system_router.get("/test/report")
async def system_report(session_id: str = Query(..., min_length=1, description="Session identifier")):
    """Returns code coverage collected for the specified test session."""
    session = cross_store.get_system_session(session_id)
    if not session:
        return JSONResponse(
            status_code=404,
            content={"message": f"Session '{session_id}' not found.", "source": "system"},
        )

    code_covered = None
    code_total = None
    code_basis = "Source lines; target instrumentation unavailable"

    cov = _system_coverage_instances.pop(session_id, None)
    if cov is not None:
        try:
            cov.stop()
            cov.save()
            data = cov.get_data()
            files = data.measured_files()
            total_stmts = 0
            covered_stmts = 0
            for f in files:
                analysis = cov._analyze(f)
                total_stmts += len(analysis.statements)
                covered_stmts += len(analysis.executed)
            if total_stmts > 0:
                code_covered = covered_stmts
                code_total = total_stmts
                code_basis = f"Source lines executed in core/ and web/ during test session ({covered_stmts}/{total_stmts} statements)"
        except Exception as e:
            code_basis = f"Source lines; live coverage calculation error: {e}"

    return {
        "session_id": session_id,
        "coverage": {
            "code": {
                "covered": code_covered,
                "total": code_total,
                "basis": code_basis,
            },
        },
    }


# --- Tester Role Endpoints ---

@tester_router.post("/test/setup", status_code=201)
async def tester_setup(req: TesterSetupRequest):
    """Prepares a test run by registering target_url and calling system setup."""
    clean_target = req.target_url.rstrip("/")
    if not clean_target.startswith("http://") and not clean_target.startswith("https://"):
        return JSONResponse(
            status_code=400,
            content={"message": "Invalid target_url scheme (must be http:// or https://).", "source": "tester"},
        )

    # 1. Create local tester session
    tester_session = cross_store.create_tester_session(clean_target)
    session_id = tester_session.session_id

    # 2. Call target system setup
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{clean_target}/test/setup",
                json={"session_id": session_id, "setup": {}},
            )
            if resp.status_code == 201:
                return JSONResponse(
                    status_code=201,
                    content={"session_id": session_id},
                )

            # Forward system error
            try:
                error_body = resp.json()
                msg = error_body.get("message", f"Target returned HTTP {resp.status_code}")
                src = error_body.get("source", "system")
            except Exception:
                msg = resp.text or f"Target returned HTTP {resp.status_code}"
                src = "system"

            return JSONResponse(
                status_code=resp.status_code,
                content={"message": msg, "source": src},
            )

    except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as exc:
        return JSONResponse(
            status_code=500,
            content={
                "message": f"Target system unreachable: {exc}",
                "source": "communication",
            },
        )
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=500,
            content={
                "message": f"Tester internal setup error: {exc}",
                "source": "tester",
            },
        )


@tester_router.post("/test/run")
async def tester_run(req: TesterRunRequest):
    """Executes the automated cross-team test suite against the target system."""
    session = cross_store.get_tester_session(req.session_id)
    if not session:
        return JSONResponse(
            status_code=404,
            content={"message": f"Unknown session ID '{req.session_id}'.", "source": "tester"},
        )

    try:
        cross_store.mark_tester_running(req.session_id)
    except ValueError as exc:
        return JSONResponse(
            status_code=409,
            content={"message": str(exc), "source": "tester"},
        )

    try:
        results, coverage = await run_cross_team_tests(session.target_url, req.session_id)
        cross_store.complete_tester_session(req.session_id, results, coverage)

        return {
            "session_id": req.session_id,
            "target_url": session.target_url,
            "results": results,
            "coverage": coverage,
        }

    except Exception as exc:  # noqa: BLE001
        abort_results = [
            {"test_id": "T-ABORT", "outcome": "error", "source": "tester", "message": f"Suite aborted: {exc}"}
        ]
        fallback_cov = {
            "code": {"covered": None, "total": None, "basis": "Target instrumentation unavailable"},
            "component": {"covered": 0, "total": 4, "basis": "4 core screening components (Metadata, Structure, Text, Images); suite aborted before execution"},
            "system": {"covered": 0, "total": 10, "basis": "10 pod acceptance criteria (AC-01..AC-04, AC-07..AC-12); suite aborted before execution"},
        }
        if is_self_target(session.target_url):
            fallback_cov["model"] = {
                "covered": 0,
                "total": 18,
                "basis": "Phase 5 Design Model v2.0; mapped against REQ-01 through REQ-18 in docs/WCAG_TAXONOMY.md and docs/ROADMAP.md",
            }
        cross_store.abort_tester_session(req.session_id, abort_results, fallback_cov, str(exc))
        return JSONResponse(
            status_code=500,
            content={"message": f"Tester aborted: {exc}", "source": "tester"},
        )


@tester_router.get("/test/report")
async def tester_report(session_id: str = Query(..., min_length=1, description="Session identifier")):
    """Retrieves stored suite report after run completion or abort."""
    session = cross_store.get_tester_session(session_id)
    if not session:
        return JSONResponse(
            status_code=404,
            content={"message": f"Unknown session ID '{session_id}'.", "source": "tester"},
        )

    if session.status in ("prepared", "running"):
        return JSONResponse(
            status_code=409,
            content={"message": f"Suite run has not completed (status='{session.status}').", "source": "tester"},
        )

    return {
        "session_id": session.session_id,
        "target_url": session.target_url,
        "results": session.results,
        "coverage": session.coverage,
    }
