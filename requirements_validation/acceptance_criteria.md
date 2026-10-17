AC-01 — REQ-01
Setup/Input: Provide a publicly reachable HTTP/HTTPS webpage and one unreachable or private URL.
Action/Check: Submit each URL for analysis.
Expected Result/Pass Rule: The public webpage is accepted and analyzed. The unreachable or private input is rejected with a reason, and the system does not crash.
Evaluation Method: Automated integration test.

AC-02 — REQ-02
Setup/Input: Provide valid PDFs below 25 MB, a PDF exactly 25 MB, a file above 25 MB, and an image-only or unreadable PDF.
Action/Check: Submit each file for analysis.
Expected Result/Pass Rule: PDFs up to and including 25 MB are accepted. Oversized files are rejected. PDFs that cannot be meaningfully analyzed are clearly identified rather than treated as accessible.
Evaluation Method: Automated test plus inspection.

AC-03 — REQ-03
Setup/Input: Use shared webpages and PDFs containing known examples involving alternative text, structure, keyboard accessibility, labels, and names or roles.
Action/Check: Run a full scan.
Expected Result/Pass Rule: The system evaluates every WCAG category included in the shared specification and associates applicable findings with the correct WCAG 2.1 criterion.
Evaluation Method: Automated comparison plus human inspection.

AC-04 — REQ-04
Setup/Input: Use test content containing deterministic conditions such as a missing alt attribute or unlabeled control.
Action/Check: Run the same scan at least three times using the same system version and unchanged input.
Expected Result/Pass Rule: Rule-based checks detect the known condition, and all repeated runs produce the same deterministic result.
Evaluation Method: Automated regression test.

AC-05 — REQ-05
Setup/Input: Provide at least one input requiring semantic judgment, such as an image with technically present but inadequate alternative text.
Action/Check: Run the AI-assisted check.
Expected Result/Pass Rule: The system returns an AI-assisted accessibility analysis for at least one supported judgment-oriented task and clearly identifies it as AI-generated.
Evaluation Method: Automated execution plus human review of relevance.

AC-06 — REQ-06
Setup/Input: Provide ambiguous content where a definite pass or fail result cannot be justified.
Action/Check: Run the supported accessibility analysis.
Expected Result/Pass Rule: The result is classified as Needs Human Review rather than being reported as a definite Pass or Issue.
Evaluation Method: Automated classification check plus human inspection.

AC-07 — REQ-07
Setup/Input: Use an input containing at least one known accessibility issue.
Action/Check: Scan the input and inspect the resulting finding.
Expected Result/Pass Rule: Each detected issue identifies the affected location, issue description, related WCAG criterion or accessibility concern, and analysis method.
Evaluation Method: Automated schema validation plus inspection.

AC-08 — REQ-08
Setup/Input: Use an input with a problem having a clear correction, such as missing alternative text.
Action/Check: Run the scan and inspect the finding.
Expected Result/Pass Rule: The finding includes reasonable remediation guidance, but the source webpage or PDF is not automatically modified.
Evaluation Method: Human inspection plus automated check that input remains unchanged.

AC-09 — REQ-09
Setup/Input: Complete a scan containing known passes, issues, human-review items, and unavailable checks.
Action/Check: Compare the summary to the individual findings.
Expected Result/Pass Rule: Summary counts for performed checks, issues, passes, human-review items, and unavailable checks match the detailed findings exactly.
Evaluation Method: Automated calculation and comparison.

AC-10 — REQ-10
Setup/Input: Use an input that passes all checks implemented by the project.
Action/Check: Generate the final report.
Expected Result/Pass Rule: The report does not claim full ADA or WCAG compliance and clearly states that only the supported subset was evaluated and additional human review may be necessary.
Evaluation Method: Automated text check plus human inspection.

AC-11 — REQ-11
Setup/Input: Submit an invalid URL, unreachable URL, non-PDF file, corrupted PDF, and file exceeding the supported limit.
Action/Check: Attempt to scan each input.
Expected Result/Pass Rule: Each invalid or unsupported input is rejected without crashing, enters the equivalent of the Rejected state, and returns a meaningful reason.
Evaluation Method: Automated negative-input tests.

AC-12 — REQ-12
Setup/Input: Use an input where some content can be analyzed but another portion cannot.
Action/Check: Run a scan that intentionally causes partial analysis.
Expected Result/Pass Rule: Valid findings are preserved. Unavailable checks are marked Could Not Evaluate or Not Tested and are not counted as Pass.
Evaluation Method: Automated fault-injection test plus inspection.

AC-13 — REQ-13
Setup/Input: Disable, mock, or force a timeout from the AI or external analysis service while deterministic checks remain available.
Action/Check: Run the scan.
Expected Result/Pass Rule: Deterministic analysis still completes, the AI-dependent portion is marked unavailable, and the scan does not completely fail when meaningful rule-based findings exist.
Evaluation Method: Automated fault-injection or integration test.

AC-14 — REQ-14
Setup/Input: Run a scan containing both deterministic and AI-assisted findings.
Action/Check: Inspect stored or output findings.
Expected Result/Pass Rule: Every finding can be traced to its source input and check, and AI-generated findings are distinguishable from deterministic findings.
Evaluation Method: Automated schema and traceability test.

AC-15 — REQ-15
Setup/Input: Upload a PDF and complete a scan.
Action/Check: Inspect storage behavior and attempt unauthenticated or public access to uploaded or extracted content.
Expected Result/Pass Rule: Uploaded or extracted content is not intentionally publicly accessible. If stored, it can be removed when no longer needed for processing.
Evaluation Method: Security test plus human inspection.

AC-16 — REQ-16
Setup/Input: Configure the system with test API credentials.
Action/Check: Inspect client responses, generated reports, deployed client code, and the public repository.
Expected Result/Pass Rule: API keys or credentials do not appear in client-side source, reports, or committed repository files.
Evaluation Method: Automated secret scan plus human inspection.

AC-17 — REQ-17
Setup/Input: Use the pod's shared webpages and PDFs containing known accessibility conditions.
Action/Check: Run the same unchanged inputs multiple times on the same system version.
Expected Result/Pass Rule: Deterministic findings remain identical across runs. AI results may differ, but they remain separately labeled so teams can compare results consistently.
Evaluation Method: Automated regression and comparison test.

AC-18 — REQ-18
Setup/Input: Use one normal webpage and one valid PDF of 25 MB or less while required third-party services are available.
Action/Check: Measure elapsed time from accepted submission until initial results are returned.
Expected Result/Pass Rule: Initial results are available within 60 seconds. If processing exceeds 60 seconds, the system visibly indicates that analysis is still in progress rather than appearing to fail.
Evaluation Method: Automated performance test plus UI or API inspection.