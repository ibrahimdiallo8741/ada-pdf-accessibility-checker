Start Webpage Scan — REQ-01, REQ-03–REQ-06, REQ-11
POST /api/scans/web
Request: {"url": "https://example.gov/page"%7D
Success 202 Accepted: {"scan_id":"S001","status":"ANALYZING"}
Errors: 400 invalid URL, 422 unsupported/inaccessible page, 500 internal error. A successful request creates a scan and begins analysis.

Start PDF Scan — REQ-02, REQ-03–REQ-06, REQ-11, REQ-15
POST /api/scans/pdf using multipart/form-data with a PDF file.
Success 202 Accepted: {"scan_id":"S002","status":"ANALYZING"}
Errors: 400 invalid/corrupted PDF, 413 file exceeds 25 MB, 415 non-PDF file, 500 internal error. Uploaded content must not be made publicly accessible.
Get Scan Status — REQ-12, REQ-13, REQ-18
GET /api/scans/{scan_id}/status
Success 200 OK: {"scan_id":"S001","status":"ANALYZING"}
Status must be one of VALIDATING, ANALYZING, GENERATING_REPORT, COMPLETED, or REJECTED. Error: 404 if the scan does not exist.

Get Scan Results — REQ-06–REQ-10, REQ-12–REQ-14, REQ-17
GET /api/scans/{scan_id}/results
Success 200 OK returns the scan summary and findings. Each finding contains finding_id, input_location, issue_description, WCAG_criterion, analysis_method, status, and remediation_guidance. Finding status must be Pass, Issue, Needs Human Review, or Could Not Evaluate; analysis method must identify Deterministic, AI, or Human Review.

Shared definitions: scan_id and finding_id are required strings and must be unique. status is a required string with allowed values VALIDATING, ANALYZING, GENERATING_REPORT, COMPLETED, or REJECTED. Finding status is required and must be Pass, Issue, Needs Human Review, or Could Not Evaluate. analysis_method is required and must be Deterministic, AI, or Human Review.

Web Scan Input: url is a required string containing a publicly reachable HTTP/HTTPS URL. Example request: {"url":"https://example.gov/page"%7D. Example response: {"scan_id":"S001","status":"ANALYZING"}.

PDF Scan Input: file is a required PDF uploaded using multipart/form-data. Maximum supported size is 25 MB. Example: file=example.pdf. Example response: {"scan_id":"S002","status":"ANALYZING"}.

Scan Results: Each finding contains required finding_id, input_location, issue_description, WCAG_criterion, analysis_method, and status. remediation_guidance and additional_details are optional strings. The summary contains required non-negative integers for checks, passed, issues, human_review, and could_not_evaluate.

Invalid-input example: Request {"url":"not-a-url"} returns 400 Bad Request with {"error":"INVALID_URL","message":"A valid HTTP or HTTPS URL is required."}. A PDF larger than 25 MB returns 413 Payload Too Large, and a non-PDF upload returns 415 Unsupported Media Type