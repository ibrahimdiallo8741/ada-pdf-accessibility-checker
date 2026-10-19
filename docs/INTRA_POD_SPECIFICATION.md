# Intra-Pod System Specification

This document defines the cross-team testing interface, current scope and limitations, and the complete OpenAPI specification for pod services.

---

## 1. Testing Interface

The cross-team testing interface conforms to the course testing specification. Each team deploys two distinguishable service roles:
- **System**: Implements `/test/setup` and `/test/report`, plus the core project API (`/api/*` and `/system/api/*`).
- **Tester**: Implements `/test/setup`, `/test/run`, and `/test/report`. The tester executes an automated test sequence against a designated target system's project API and collects coverage.

Base URLs must be distinguishable by subpath:
- **System Base URL**: `https://<HOST>/system` (or `/` alias)
- **Tester Base URL**: `https://<HOST>/tester`

### Suite Report Schema

```json
{
  "session_id": "run-123",
  "target_url": "https://team-target.example.edu/system",
  "results": [
    {
      "test_id": "T-01",
      "outcome": "pass",
      "message": "Valid accessible PDF screening returned HTTP 202 and COMPLETED status."
    },
    {
      "test_id": "T-06",
      "outcome": "pass",
      "message": "Corrupted PDF bytes were rejected with HTTP 400 Bad Request."
    },
    {
      "test_id": "T-10",
      "outcome": "error",
      "source": "communication",
      "message": "Target endpoint timed out after 30 seconds."
    }
  ],
  "coverage": {
    "code": {
      "covered": null,
      "total": null,
      "basis": "Source lines; target instrumentation unavailable"
    },
    "component": {
      "covered": 3,
      "total": 3,
      "basis": "Core Screening Engine, In-Memory Storage, REST API Delivery"
    },
    "system": {
      "covered": 10,
      "total": 18,
      "basis": "Acceptance criteria AC-01 through AC-18 evaluated by suite"
    }
  }
}
```

- **Allowed Outcomes**: `pass`, `fail`, `error`, `skip`.
- **Allowed Error Sources**: `tester`, `system`, `communication`, `unknown`.
- **Coverage Rules**: If a coverage measure cannot be evaluated, `covered` and `total` MUST be `null` (never substituted with `0`), and `basis` must contain an explanatory string.

---

## 2. Current Scope and Limitations

### 2.1 Current Scope

1. **Target Medium & Size**:
   - Digital PDF documents (ISO 32000-1) up to 25 MB in size.
   - Files exceeding 25 MB are rejected with `413 Payload Too Large`.
   - Empty files (0 bytes) are rejected with `400 Bad Request`.
   - Non-PDF files are rejected with `415 Unsupported Media Type`.
2. **Zero-Disk In-Memory Processing**:
   - All uploaded documents stream exclusively through memory buffers (`io.BytesIO`).
   - Files are never written to disk, `/tmp`, or cloud storage.
   - Buffer memory references are released immediately upon screening completion for garbage collection.
3. **Deterministic WCAG 2.1 Level AA Rules Evaluated**:
   - **2.4.2 Page Titled (Level A)**: Verifies presence and non-emptiness of document metadata title.
   - **3.1.1 Language of Page (Level A)**: Verifies presence of natural language code in document catalog dictionary (`/Lang`).
   - **1.3.1 Info and Relationships (Level A)**: Verifies structural tagging root existence (`/StructTreeRoot` dictionary in catalog).
   - **1.4.5 Images of Text (Level AA)**: Verifies presence of extractable digital text streams across all document pages to flag scanned bitmap documents.
   - **1.1.1 Non-text Content (Level A)**: Discovers and counts embedded raster image resources (`/XObject` of subtype `/Image`).
4. **Standardized Finding Taxonomy**:
   - Every finding is classified into exactly one of four normalized statuses:
     - `Pass`: Criterion heuristic satisfied.
     - `Issue`: Concrete accessibility barrier detected.
     - `Needs Human Review`: Element detected requiring subjective human assessment.
     - `Could Not Evaluate`: File encryption, corruption, or parser exception prevented evaluation.
5. **Actionable Remediation Guidance**:
   - Every non-passing finding (`Issue`, `Needs Human Review`, `Could Not Evaluate`) includes concrete remediation instructions.
6. **Delivery Interfaces**:
   - Asynchronous REST API with polling status lifecycle (`VALIDATING` → `ANALYZING` → `COMPLETED` / `REJECTED`).
   - Cross-team testing endpoints (`/system/test/*` and `/tester/test/*`).
   - Interactive browser application at `/`.

### 2.2 Operational Limitations & Screening Boundaries

1. **Preliminary screener only**:
   - The tool performs preliminary automated heuristic screening. Passing automated checks does not certify legal compliance with ADA Title II, Section 508, or WCAG 2.1 Level AA.
2. **Webpage Scanning Not Yet Supported**:
   - Webpage scanning (`POST /api/scans/web`) is descoped from the active prototype and returns `422 Unprocessable Entity`.
3. **Structure Tree Root vs. Semantic Tag Quality (WCAG 1.3.1)**:
   - Validating `/StructTreeRoot` presence proves a structure dictionary exists; it does not prove correct semantic tag usage (`<h1>`–`<h6>`, `<table>`, `<l>`, `<th>` vs `<td>`) or logical reading order.
4. **Image Resource Count vs. Alternative Text Quality (WCAG 1.1.1)**:
   - Discovering raster image resources flags images for inspection; it does not inspect whether `/Alt` attributes exist on structure elements or whether descriptions are contextually accurate.
5. **Extractable Character Streams vs. Assistive Usability (WCAG 1.4.5)**:
   - Confirming digital text presence does not evaluate screen reader reading order, pronunciation correctness, or table navigation.
6. **AI Heuristics Deferred**:
   - Multimodal and LLM-assisted accessibility heuristics (e.g. contextual image description evaluation, reading order coherence) are deferred. All active checks are deterministic.
7. **Session Concurrency**:
   - Cross-team testing operations are executed sequentially to avoid resource contention across single-worker peer hosting deployments.
8. **In-Memory Retention TTL**:
   - Scan jobs and test session records expire and are evicted from in-memory registries after 1 hour (3600 seconds).

---

## 3. OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: ADA PDF Accessibility Screening API
  description: >-
    Automated screening prototype aligned with ADA Title II and WCAG 2.1 Level
    AA.
  version: 0.1.0
paths:
  /:
    get:
      tags:
        - Web UI
      summary: Get Index
      description: Serves the interactive screening portal and automated test runner.
      operationId: get_index__get
      responses:
        '200':
          description: Successful Response
          content:
            text/html:
              schema:
                type: string
  /api/scans/pdf:
    post:
      tags:
        - Scans
      summary: Start Pdf Scan
      description: >-
        Submits a PDF for asynchronous accessibility screening (REQ-02, REQ-03,
        REQ-12, REQ-15).
      operationId: start_pdf_scan_api_scans_pdf_post
      requestBody:
        content:
          multipart/form-data:
            schema:
              $ref: '#/components/schemas/Body_start_pdf_scan_api_scans_pdf_post'
        required: true
      responses:
        '202':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/scans/web:
    post:
      tags:
        - Scans
      summary: Start Web Scan
      description: >-
        Web scan endpoint (descoped for prototype per REQ-12 and
        FUTURE_WORK.md).
      operationId: start_web_scan_api_scans_web_post
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/WebScanRequest'
        required: true
      responses:
        '422':
          description: Successful Response
          content:
            application/json:
              schema: {}
  '/api/scans/{scan_id}/status':
    get:
      tags:
        - Scans
      summary: Get Scan Status
      description: >-
        Returns the current processing status of a scan job (REQ-12, REQ-13,
        REQ-18).
      operationId: get_scan_status_api_scans__scan_id__status_get
      parameters:
        - name: scan_id
          in: path
          required: true
          schema:
            type: string
            title: Scan Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  '/api/scans/{scan_id}/results':
    get:
      tags:
        - Scans
      summary: Get Scan Results
      description: >-
        Retrieves completed accessibility findings and summary counts
        (REQ-06–REQ-10, REQ-17).
      operationId: get_scan_results_api_scans__scan_id__results_get
      parameters:
        - name: scan_id
          in: path
          required: true
          schema:
            type: string
            title: Scan Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/test-runner:
    get:
      tags:
        - Scans
        - Test Runner
      summary: Trigger Automated Tests
      description: >-
        Runs automated acceptance test suite against curated test fixtures
        (AC-01 through AC-18).
      operationId: trigger_automated_tests_api_test_runner_get
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
    post:
      tags:
        - Scans
        - Test Runner
      summary: Trigger Automated Tests
      description: >-
        Runs automated acceptance test suite against curated test fixtures
        (AC-01 through AC-18).
      operationId: trigger_automated_tests_api_test_runner_post
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
  /system/api/scans/pdf:
    post:
      tags:
        - Scans
      summary: Start Pdf Scan
      description: >-
        Submits a PDF for asynchronous accessibility screening (REQ-02, REQ-03,
        REQ-12, REQ-15).
      operationId: start_pdf_scan_system_api_scans_pdf_post
      requestBody:
        content:
          multipart/form-data:
            schema:
              $ref: >-
                #/components/schemas/Body_start_pdf_scan_system_api_scans_pdf_post
        required: true
      responses:
        '202':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /system/api/scans/web:
    post:
      tags:
        - Scans
      summary: Start Web Scan
      description: >-
        Web scan endpoint (descoped for prototype per REQ-12 and
        FUTURE_WORK.md).
      operationId: start_web_scan_system_api_scans_web_post
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/WebScanRequest'
        required: true
      responses:
        '422':
          description: Successful Response
          content:
            application/json:
              schema: {}
  '/system/api/scans/{scan_id}/status':
    get:
      tags:
        - Scans
      summary: Get Scan Status
      description: >-
        Returns the current processing status of a scan job (REQ-12, REQ-13,
        REQ-18).
      operationId: get_scan_status_system_api_scans__scan_id__status_get
      parameters:
        - name: scan_id
          in: path
          required: true
          schema:
            type: string
            title: Scan Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  '/system/api/scans/{scan_id}/results':
    get:
      tags:
        - Scans
      summary: Get Scan Results
      description: >-
        Retrieves completed accessibility findings and summary counts
        (REQ-06–REQ-10, REQ-17).
      operationId: get_scan_results_system_api_scans__scan_id__results_get
      parameters:
        - name: scan_id
          in: path
          required: true
          schema:
            type: string
            title: Scan Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /system/api/test-runner:
    get:
      tags:
        - Scans
        - Test Runner
      summary: Trigger Automated Tests
      description: >-
        Runs automated acceptance test suite against curated test fixtures
        (AC-01 through AC-18).
      operationId: trigger_automated_tests_system_api_test_runner_get
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
    post:
      tags:
        - Scans
        - Test Runner
      summary: Trigger Automated Tests
      description: >-
        Runs automated acceptance test suite against curated test fixtures
        (AC-01 through AC-18).
      operationId: trigger_automated_tests_system_api_test_runner_post
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
  /system/test/setup:
    post:
      tags:
        - Cross-Team System Interface
      summary: System Setup
      description: >-
        Initializes session resources on the target system
        (docs/student-facing-spec.md).
      operationId: system_setup_system_test_setup_post
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SystemSetupRequest'
        required: true
      responses:
        '201':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /system/test/report:
    get:
      tags:
        - Cross-Team System Interface
      summary: System Report
      description: Returns code coverage collected for the specified test session.
      operationId: system_report_system_test_report_get
      parameters:
        - name: session_id
          in: query
          required: true
          schema:
            type: string
            description: Session identifier
            title: Session Id
          description: Session identifier
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /test/setup:
    post:
      tags:
        - Cross-Team System Interface
      summary: System Setup
      description: >-
        Initializes session resources on the target system
        (docs/student-facing-spec.md).
      operationId: system_setup_test_setup_post
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SystemSetupRequest'
        required: true
      responses:
        '201':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /test/report:
    get:
      tags:
        - Cross-Team System Interface
      summary: System Report
      description: Returns code coverage collected for the specified test session.
      operationId: system_report_test_report_get
      parameters:
        - name: session_id
          in: query
          required: true
          schema:
            type: string
            description: Session identifier
            title: Session Id
          description: Session identifier
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /tester/test/setup:
    post:
      tags:
        - Cross-Team Tester Interface
      summary: Tester Setup
      description: Prepares a test run by registering target_url and calling system setup.
      operationId: tester_setup_tester_test_setup_post
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TesterSetupRequest'
        required: true
      responses:
        '201':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /tester/test/run:
    post:
      tags:
        - Cross-Team Tester Interface
      summary: Tester Run
      description: Executes the automated cross-team test suite against the target system.
      operationId: tester_run_tester_test_run_post
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TesterRunRequest'
        required: true
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /tester/test/report:
    get:
      tags:
        - Cross-Team Tester Interface
      summary: Tester Report
      description: Retrieves stored suite report after run completion or abort.
      operationId: tester_report_tester_test_report_get
      parameters:
        - name: session_id
          in: query
          required: true
          schema:
            type: string
            description: Session identifier
            title: Session Id
          description: Session identifier
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
components:
  schemas:
    Body_start_pdf_scan_api_scans_pdf_post:
      properties:
        file:
          type: string
          contentMediaType: application/octet-stream
          title: File
      type: object
      required:
        - file
      title: Body_start_pdf_scan_api_scans_pdf_post
    Body_start_pdf_scan_system_api_scans_pdf_post:
      properties:
        file:
          type: string
          contentMediaType: application/octet-stream
          title: File
      type: object
      required:
        - file
      title: Body_start_pdf_scan_system_api_scans_pdf_post
    HTTPValidationError:
      properties:
        detail:
          items:
            $ref: '#/components/schemas/ValidationError'
          type: array
          title: Detail
      type: object
      title: HTTPValidationError
    SystemSetupRequest:
      properties:
        session_id:
          type: string
          title: Session Id
          description: Unique session identifier for the test run
        setup:
          additionalProperties: true
          type: object
          title: Setup
          description: Initial setup parameters
      type: object
      required:
        - session_id
      title: SystemSetupRequest
    TesterRunRequest:
      properties:
        session_id:
          type: string
          title: Session Id
          description: Unique session identifier generated during tester setup
      type: object
      required:
        - session_id
      title: TesterRunRequest
    TesterSetupRequest:
      properties:
        target_url:
          type: string
          title: Target Url
          description: Base URL of the target system under test
      type: object
      required:
        - target_url
      title: TesterSetupRequest
    ValidationError:
      properties:
        loc:
          items:
            anyOf:
              - type: string
              - type: integer
          type: array
          title: Location
        msg:
          type: string
          title: Message
        type:
          type: string
          title: Error Type
        input:
          title: Input
        ctx:
          type: object
          title: Context
      type: object
      required:
        - loc
        - msg
        - type
      title: ValidationError
    WebScanRequest:
      properties:
        url:
          type: string
          title: Url
      type: object
      required:
        - url
      title: WebScanRequest
```

