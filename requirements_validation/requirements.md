### REQ-01 — Supported Web Input 
When a user submits a publicly reachable HTTP or HTTPS webpage URL, the system shall retrieve and analyze that webpage for the accessibility checks defined by the specification.
Need/source: Enables evaluation of web content covered by 28 C.F.R. § 35.200, which requires covered public-entity web content to conform to WCAG 2.1 Level AA.

### REQ-02 - Unsupported Web Content 
If a page requires authentication, payment, or access to a separate private network, then the compliance checker shall bypass it and continue.
Need/source: Authentication and payment processing are out of scope.

### REQ-03 — Supported PDF Input 
When a PDF file is submitted, the compliance checker shall analyze the PDF for the accessibility checks applicable to the project's supported PDF scope. PDF files larger than 500 MB or whose content cannot be meaningfully analyzed, such as image-only documents without usable text or structural information, are not supported.
Need/source: DOJ defines web content broadly enough to include conventional electronic documents and states that WCAG 2.1 Level AA generally applies to them to the extent the criteria can be applied. Large and complex PDFs are excluded to control scope.

### REQ-04 — Defined WCAG Test Set 
For every successful scan, the system shall evaluate a documented subset of WCAG 2.1 Level A and AA requirements. This subset shall include text alternatives (§1.1), adaptability (§1.3 except for §1.3.2-1.3.4 and §1.3.6), document/page structure (§2.4.1-2.4.7), keyboard accessibility (§2.1.1, §2.1.4), form/control labeling (§2.5.3), readability (§3.1.1-3.1.2), input assistance (§3.3.1-3.3.3) and programmatically determinable names or roles (§4.1). The report shall identify the WCAG success criterion associated with each supported check.
Need/source: Title II incorporates WCAG 2.1 Level AA as the technical accessibility standard. WCAG 2.1 Level AA was assessed for what scope of compliance was reasonable for the allowed time.

### REQ-05 — Deterministic Accessibility Checks
Where an accessibility condition can be evaluated programmatically, the system shall perform a rule-based check rather than relying solely on generative AI. Examples include detecting missing alternative-text attributes, missing document language information, unlabeled interface controls, or missing structural information.
Need/source: Provides repeatable evidence for WCAG-related requirements and reduces reliance on nondeterministic AI output. WCAG success criteria are intended to be testable through automated or manual processes. 

### REQ-06 — AI-Assisted Accessibility Analysis 
For accessibility issues requiring semantic or contextual judgment, the system shall be capable of using GenAI to provide additional analysis. Supported AI analysis shall include at least one judgment-oriented accessibility task, such as assessing whether alternative text meaningfully represents an image, identifying likely structural problems, evaluating content descriptions, or explaining why an issue may affect an assistive-technology user. 
Need/source: Stakeholder need. Automated rules alone cannot determine all accessibility properties, particularly where the adequacy or meaning of content must be interpreted. 

### REQ-07 — Human-Review Identification When the system cannot determine an accessibility result with sufficient confidence, or when the relevant WCAG requirement requires subjective judgment, the system shall classify the finding as Needs Human Review rather than reporting it as a definite pass or failure. 
Need/source: Generative AIs can hallucinate, so human review is required to verify the assessment is correct. -

### REQ-08 — Accessibility Finding Information For every detected accessibility problem, the system shall provide at least: 
(a) the affected page, document, or element; 
(b) a description of the issue; 
(c) the associated WCAG criterion or accessibility concern; and 
(d) whether the result came from an automated check, AI analysis, or requires human review. 
Need/source: Supports developers and accessibility staff who must identify and correct barriers and demonstrate how digital content was evaluated. 

### REQ-09 — Remediation Guidance 
For each detected issue where a reasonable correction can be described, the system shall provide a remediation recommendation. Recommendations shall be presented as guidance and shall not modify the original webpage or PDF automatically.
Need/source: Stakeholder need to make findings actionable while keeping content up to the owner.

### REQ-10 — Scan Summary 
After completing an analysis, the system shall produce a summary containing the number of checks performed, detected issues, passed checks, items requiring human review, and checks that could not be performed. 
Need/source: Stakeholder need for understandable accessibility status and evidence of what the system actually evaluated. -

### REQ-11 — No False Compliance Certification 
The system shall not state that a webpage, PDF, organization, or service is fully “ADA compliant” solely because it passes the implemented checks. Reports shall identify that the system evaluates only the supported subset of WCAG criteria and that additional human evaluation may be required. 
Need/source: Title II requires conformance to applicable WCAG 2.1 Level A and AA criteria, while this project intentionally checks only a subset of A and AA.


## Failure and Input Requirements
### REQ-12 — Invalid and Unsupported Input Handling 
When input is malformed, inaccessible, unsupported, or outside the defined scope, the system shall reject the input without crashing and provide the user with a reason. Examples include invalid URLs, non-PDF files submitted as PDFs, unreachable webpages, corrupted PDFs, and files exceeding the supported size limit. 
Need/source: Robustness in the face of typos or user mistakes. 

### REQ-13 — Partial Analysis Handling 
When only part of an input can be analyzed, the system shall preserve valid findings and clearly identify which checks or content could not be evaluated rather than silently treating untested content as accessible. 
Need/source: Prevents incomplete analysis from being mistaken for evidence of accessibility. 

### REQ-14 — External AI or Tool Failure 
If an AI service or external accessibility-analysis component fails, times out, or returns an unusable response, the system shall continue any analysis that does not depend on that component and shall identify the unavailable analysis in the final report.
Need/source: Reliability requirement because implementations may depend on third-party APIs and services.

## Data, Security, and Quality Requirements
### REQ-15 — Result Traceability 
Each finding shall retain enough information to determine which input produced it and which check or analysis method generated the finding. AI-generated findings shall be distinguishable from deterministic findings. 
Need/source: Need for validation, debugging, and assessing trustworthiness of findings.

### REQ-16 — Uploaded Content Protection 
The system shall not intentionally make uploaded PDFs or extracted content publicly accessible. If uploaded files or extracted content are stored, they shall be accessible only as necessary for processing and shall be deletable when no longer required for the scan. 
Need/source: Security and privacy need arising from processing potentially sensitive government or institutional documents. 

### REQ-17 — Secret and Credential Protection 
API keys, AI-service credentials, and other secrets shall not be embedded in client-side source code, committed to the public source repository, or included in accessibility reports. 
Need/source: Security requirement for systems integrating external GenAI and analysis services. 

### REQ-18 — Repeatable Evaluation Dataset 
A stable and defined set of webpages and PDFs containing known accessibility conditions shall be used for evaluation purposes. Repeated scans of unchanged input using the same system version shall produce the same pass/fail findings. AI-generated findings may vary but shall be separately identified for comparison. 
Need/source: Stakeholder need created by the course requirement that independently developed implementations produce outputs that can be compared.

### REQ-19 — Usable Results 
A successful scan shall produce its initial results within 60 seconds for a normal test input consisting of one webpage or one PDF of 25 MB or less, excluding delays caused by unavailable third-party services. If processing exceeds that limit, the interface shall indicate that analysis is still in progress rather than appearing to have failed. 
Need/source: Quality/usability requirement. The exact performance limit is a project constraint rather than a regulatory requirement.