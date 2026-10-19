# Architecture & Behavioral Diagrams

This directory contains visual and text-based architectural and behavioral models of the ADA PDF Accessibility Checker application.

> **Note**: Diagrams are defined in the standalone `.mmd` files in this directory as the single source of truth. Running `python3 scripts/sync_diagrams.py` automatically synchronizes any updates to `.mmd` files into this document.

---

## 1. System Architecture and Data Flow

**Source**: [`architecture_diagram.mmd`](architecture_diagram.mmd) (updates [`architecture_diagram.jpg`](architecture_diagram.jpg))

<!-- BEGIN:architecture_diagram -->
```mermaid
flowchart TD
    %% User / Actor
    User["<b>User / Cross-Team Tester</b><br/>(Automated test harness or human review)"]
    
    User -->|"<b>HTTP Requests</b><br/>POST /api/scans/pdf<br/>POST /api/scans/web<br/>GET /api/scans/{id}/status<br/>GET /api/scans/{id}/results"| APILayer

    %% API Layer
    APILayer["⚙️ <b>API / Request Layer</b><br/>(FastAPI Common Web-Service Interface)"]
    
    APILayer --> InValidation["🛡️ <b>Input Validation Layer</b><br/>(Validate file type, <= 25 MB size limit, magic bytes)"]

    %% Branching
    InValidation -->|"Webpage URL"| WebDescoped["🌐 <b>Webpage Handler (Descoped)</b><br/>(Returns HTTP 422 Unprocessable Entity)"]
    InValidation -->|"PDF File Bytes"| PDFParser["📄 <b>In-Memory PDF Parser</b><br/>(PyMuPDF & pypdf Dual Engine Extraction)"]

    PDFParser --> ExtractedContent["📋 <b>Extracted Content + Structure</b><br/>(In-memory buffer, character streams, catalog dictionaries)"]

    %% Document Analysis Subsystem
    subgraph DocAnalysis ["Document Analysis"]
        direction LR
        RuleChecker["📝 <b>Deterministic WCAG Rule Checker</b><br/>(2.4.2 Title, 3.1.1 Lang, 1.3.1 StructTree,<br/>1.4.5 Page Text, 1.1.1 Image Discovery)"]
        AIAnalyzer["🧠 <b>AI-Assisted Analyzer</b><br/>(Deferred to future milestone;<br/>Semantic & Contextual Alt-Text Checks)"]
    end

    ExtractedContent --> RuleChecker
    ExtractedContent -.->|"Future Integration"| AIAnalyzer

    RuleChecker --> FindingProc["🗂️ <b>Finding Processor</b><br/>(Classify: Pass | Issue | Needs Human Review | Could Not Evaluate)"]

    FindingProc --> ReportGen["📑 <b>Report Generator</b><br/>(ScanSummary arithmetic, detailed findings, remediation guidance)"]

    ReportGen --> ResStorage[("💾 <b>In-Memory Result Storage</b><br/>(Zero-disk stream buffer, 1-hour TTL auto-eviction)")]

    APILayer -.->|"GET /api/scans/{id} (polling & results)"| ResStorage

    ResStorage --> APIResp["↩️ <b>API Response</b><br/>(Scan ID, status enum, or complete ScanReport JSON)"]

    %% Styling classes matching original pastel palette
    classDef actorStyle fill:#cbe2f8,stroke:#6ca0dc,stroke-width:2px,color:#1e3a8a;
    classDef apiStyle fill:#dfd2f7,stroke:#a88ee8,stroke-width:2px,color:#4c1d95;
    classDef validationStyle fill:#cdeed3,stroke:#7cc88b,stroke-width:2px,color:#064e3b;
    classDef inputStyle fill:#fedcc1,stroke:#f69d64,stroke-width:2px,color:#7c2d12;
    classDef analysisStyle fill:#fecdd2,stroke:#f48fb1,stroke-width:2px,color:#831843;
    classDef findingStyle fill:#fef0b8,stroke:#ebd069,stroke-width:2px,color:#78350f;
    classDef storageStyle fill:#bbf2c8,stroke:#5bbd70,stroke-width:2px,color:#064e3b;
    classDef respStyle fill:#cbe2f8,stroke:#6ca0dc,stroke-width:2px,color:#1e3a8a;

    class User actorStyle;
    class APILayer,ReportGen apiStyle;
    class InValidation,ExtractedContent validationStyle;
    class WebDescoped,PDFParser inputStyle;
    class RuleChecker,AIAnalyzer analysisStyle;
    class FindingProc findingStyle;
    class ResStorage storageStyle;
    class APIResp respStyle;

    style DocAnalysis fill:#fff5f5,stroke:#e57373,stroke-width:2px,stroke-dasharray: 6 6;
```
<!-- END:architecture_diagram -->

---

## 2. Accessibility Scan Workflow (Model 1)

**Source**: [`scan_workflow.mmd`](scan_workflow.mmd) (updates [`Behavioral_information_model.png`](Behavioral_information_model.png))

<!-- BEGIN:scan_workflow -->
```mermaid
flowchart TD
    Start["User submits input<br/>(PDF upload)"]
    ValCheck{"Validate input<br/>(Size <= 25MB, format, header)"}
    ErrStop["<b>Show error / reason</b><br/>Stop scan (Return 400, 413, 415, or 422)"]
    TypeCheck{"Identify input type"}
    WebBranch["<b>Webpage input</b><br/>Return 422 (Descoped for prototype)"]
    Extract["<b>Extract accessible content</b><br/>(In-memory PyMuPDF & pypdf byte stream)"]
    RunRules["<b>Run deterministic WCAG checks</b><br/>(Title, Lang, StructTree, Text, Images)"]
    Classify["<b>Classify each finding</b><br/>(Pass | Issue | Needs Human Review | Could Not Evaluate)"]
    Remed["<b>Generate remediation guidance</b><br/>(Actionable steps for non-passing items)"]
    GenReport["<b>Generate final report + scan summary</b><br/>(Findings, counts, and zero-disk cache)"]

    Start --> ValCheck
    ValCheck -->|Invalid| ErrStop
    ValCheck -->|Valid| TypeCheck
    TypeCheck -->|Webpage| WebBranch
    TypeCheck -->|PDF| Extract
    Extract --> RunRules
    RunRules --> Classify
    Classify --> Remed
    Remed --> GenReport

    classDef blueBox fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e3a8a;
    classDef yellowCond fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,color:#78350f;
    classDef redStop fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#991b1b;
    classDef greenStep fill:#dcfce7,stroke:#22c55e,stroke-width:2px,color:#14532d;

    class Start,TypeCheck,Extract,Classify,Remed,GenReport blueBox;
    class ValCheck yellowCond;
    class ErrStop,WebBranch,AIFallback redStop;
    class RunRules,RunAI greenStep;
```
<!-- END:scan_workflow -->

---

## 3. Finding Data Model (Model 2)

**Source**: [`finding_data_model.mmd`](finding_data_model.mmd)

<!-- BEGIN:finding_data_model -->
```mermaid
classDiagram
    class ScanReport {
        +string scan_id
        +string file
        +int pages
        +ScanSummary summary
        +List~Finding~ findings
        +to_dict() dict
    }

    class ScanSummary {
        +int checks
        +int passed
        +int issues
        +int human_review
        +int could_not_evaluate
        +to_dict() dict
    }

    class Finding {
        +string finding_id
        +string input_location
        +string issue_description
        +string WCAG_criterion
        +string analysis_method
        +string status
        +string remediation_guidance
        +string additional_details
        +to_dict() dict
    }

    ScanReport *-- ScanSummary
    ScanReport *-- Finding
```
<!-- END:finding_data_model -->

---

## 4. Scan State Lifecycle Model (Model 3)

**Source**: [`scan_state_model.mmd`](scan_state_model.mmd)

<!-- BEGIN:scan_state_model -->
```mermaid
flowchart TD
    Submitted["<b>SUBMITTED</b><br/>(POST /api/scans/pdf)"]
    Validating["<b>VALIDATING</b><br/>(Inspect size <= 25MB, MIME, PDF magic bytes)"]
    Rejected["<b>REJECTED</b><br/>(Show error reason: 400, 413, 415)"]
    Analyzing["<b>ANALYZING</b><br/>(Run deterministic WCAG rule checks)"]
    PartialFail["<b>Record Limitation</b><br/>(Partial failure fallback: e.g. unparseable tags)"]
    GenReport["<b>GENERATING REPORT</b><br/>(Summarize findings, arithmetic counts & remediation)"]
    Completed["<b>COMPLETED</b><br/>(Results available in-memory, 1-hour TTL)"]

    Submitted --> Validating
    Validating -->|"Invalid input"| Rejected
    Validating -->|"Valid input (202 Accepted)"| Analyzing
    Analyzing -.->|"Partial failure"| PartialFail
    PartialFail -.-> Analyzing
    Analyzing -->|"All checks completed"| GenReport
    GenReport -->|"Report stored"| Completed

    %% Styling classes matching architecture_diagram.mmd and scan_workflow.mmd conventions
    classDef actorStyle fill:#cbe2f8,stroke:#6ca0dc,stroke-width:2px,color:#1e3a8a;
    classDef validationStyle fill:#cdeed3,stroke:#7cc88b,stroke-width:2px,color:#064e3b;
    classDef analysisStyle fill:#fecdd2,stroke:#f48fb1,stroke-width:2px,color:#831843;
    classDef findingStyle fill:#fef0b8,stroke:#ebd069,stroke-width:2px,color:#78350f;
    classDef apiStyle fill:#dfd2f7,stroke:#a88ee8,stroke-width:2px,color:#4c1d95;
    classDef storageStyle fill:#bbf2c8,stroke:#5bbd70,stroke-width:2px,color:#064e3b;
    classDef errorStyle fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#991b1b;

    class Submitted actorStyle;
    class Validating validationStyle;
    class Analyzing analysisStyle;
    class Rejected errorStyle;
    class PartialFail findingStyle;
    class GenReport apiStyle;
    class Completed storageStyle;
```
<!-- END:scan_state_model -->
