import asyncio
from unittest.mock import AsyncMock, patch

import httpx
from web.cross_team_storage import cross_store


def _get_app():
    from web.app import app
    return app


def _run(coro):
    return asyncio.run(coro)


def test_system_setup_and_report_lifecycle() -> tuple[bool, str]:
    """Tests System role /test/setup and /test/report endpoints."""
    async def _async_test():
        app = _get_app()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
            # 1. Successful setup
            s_id = "sys-test-001"
            resp = await client.post("/system/test/setup", json={"session_id": s_id, "setup": {}})
            if resp.status_code != 201 or resp.json().get("session_id") != s_id:
                return False, f"Expected 201 with session_id, got {resp.status_code}: {resp.text}"

            # 2. Duplicate setup returns 409
            dup_resp = await client.post("/system/test/setup", json={"session_id": s_id, "setup": {}})
            if dup_resp.status_code != 409 or dup_resp.json().get("source") != "system":
                return False, f"Expected 409 on duplicate setup, got {dup_resp.status_code}"

            # 3. Valid report lookup
            rep_resp = await client.get("/system/test/report", params={"session_id": s_id})
            if rep_resp.status_code != 200:
                return False, f"Expected 200 on system report, got {rep_resp.status_code}"
            rep_data = rep_resp.json()
            if "coverage" not in rep_data or "code" not in rep_data["coverage"]:
                return False, f"System report missing code coverage structure: {rep_data}"

            # 4. Unknown session returns 404
            missing_resp = await client.get("/system/test/report", params={"session_id": "nonexistent-999"})
            if missing_resp.status_code != 404:
                return False, f"Expected 404 for unknown session, got {missing_resp.status_code}"

            # 5. Root alias /test/setup and /test/report
            root_s_id = "root-test-001"
            root_resp = await client.post("/test/setup", json={"session_id": root_s_id, "setup": {}})
            if root_resp.status_code != 201:
                return False, f"Root alias /test/setup failed: {root_resp.status_code}"
            root_rep = await client.get("/test/report", params={"session_id": root_s_id})
            if root_rep.status_code != 200:
                return False, f"Root alias /test/report failed: {root_rep.status_code}"

            return True, "System /test/setup and /test/report endpoints conform to spec."

    return _run(_async_test())


def test_system_dual_mount_api() -> tuple[bool, str]:
    """Tests that project API is accessible under /system/api as well as /api."""
    async def _async_test():
        app = _get_app()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
            resp1 = await client.get("/api/scans/MISSING/status")
            resp2 = await client.get("/system/api/scans/MISSING/status")
            if resp1.status_code != 404 or resp2.status_code != 404:
                return False, f"Dual mount mismatch: /api={resp1.status_code}, /system/api={resp2.status_code}"

            web_resp = await client.post("/system/api/scans/web", json={"url": "https://example.com"})
            if web_resp.status_code != 422:
                return False, f"Expected 422 for web scan under /system/api, got {web_resp.status_code}"

            return True, "Project API successfully dual-mounted under /api and /system/api."

    return _run(_async_test())


def test_tester_setup_target_communication() -> tuple[bool, str]:
    """Tests Tester setup error handling and communication failure classification."""
    async def _async_test():
        app = _get_app()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
            # 1. Invalid scheme
            bad_scheme = await client.post("/tester/test/setup", json={"target_url": "ftp://bad-url"})
            if bad_scheme.status_code != 400:
                return False, f"Expected 400 for bad URL scheme, got {bad_scheme.status_code}"

            # 2. Unreachable target returns 500 with source: communication
            unreachable = await client.post("/tester/test/setup", json={"target_url": "http://127.0.0.1:54321/system"})
            if unreachable.status_code != 500 or unreachable.json().get("source") != "communication":
                return False, f"Expected 500 communication error for unreachable target, got {unreachable.status_code}: {unreachable.text}"

            return True, "Tester setup properly validates URLs and classifies communication errors."

    return _run(_async_test())


def test_tester_run_and_report_lifecycle() -> tuple[bool, str]:
    """Tests Tester suite execution against local system via ASGITransport and report retrieval."""
    async def _async_test():
        app = _get_app()
        # Setup session in cross_store pointing to test server
        tester_session = cross_store.create_tester_session("http://testserver/system")
        session_id = tester_session.session_id

        # Register system session on the target as well
        cross_store.register_system_session(session_id)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
            # Report lookup before run returns 409
            early_rep = await client.get("/tester/test/report", params={"session_id": session_id})
            if early_rep.status_code != 409:
                return False, f"Expected 409 before run completes, got {early_rep.status_code}"

            # Execute run with httpx ASGITransport patched into http_cross_tester
            transport = httpx.ASGITransport(app=app)
            real_async_client = httpx.AsyncClient

            def mock_client(*args, **kwargs):
                kwargs["transport"] = transport
                return real_async_client(*args, **kwargs)

            with patch("tests.http_cross_tester.httpx.AsyncClient", side_effect=mock_client):
                run_resp = await client.post("/tester/test/run", json={"session_id": session_id})

            if run_resp.status_code != 200:
                return False, f"Tester run failed with HTTP {run_resp.status_code}: {run_resp.text}"

            run_data = run_resp.json()
            results = run_data.get("results", [])
            coverage = run_data.get("coverage", {})

            if len(results) != 10:
                return False, f"Expected 10 test results (T-01..T-10), got {len(results)}"

            passed_tests = [r for r in results if r.get("outcome") == "pass"]
            if len(passed_tests) < 10:
                fails = [r for r in results if r.get("outcome") != "pass"]
                return False, f"Not all tests passed against local system: {fails}"

            # Verify coverage structure
            if coverage.get("component", {}).get("covered") != 4:
                return False, f"Component coverage unexpected: {coverage}"
            if "Document Metadata Inspector" not in coverage.get("component", {}).get("basis", ""):
                return False, f"Component basis lacks detailed component names: {coverage.get('component')}"
            if coverage.get("system", {}).get("covered") != 10:
                return False, f"System coverage unexpected: {coverage}"
            if "AC-01" not in coverage.get("system", {}).get("basis", ""):
                return False, f"System basis lacks detailed criteria names: {coverage.get('system')}"

            # Duplicate run returns 409
            dup_run = await client.post("/tester/test/run", json={"session_id": session_id})
            if dup_run.status_code != 409:
                return False, f"Expected 409 on duplicate run, got {dup_run.status_code}"

            # Subsequent report lookup returns 200 with identical report
            stored_rep = await client.get("/tester/test/report", params={"session_id": session_id})
            if stored_rep.status_code != 200:
                return False, f"Stored report lookup failed: {stored_rep.status_code}"
            if len(stored_rep.json().get("results", [])) != 10:
                return False, "Stored report results count mismatch."

            return True, "Tester run executed 10/10 test cases, computed coverage, and persisted report."

    return _run(_async_test())
