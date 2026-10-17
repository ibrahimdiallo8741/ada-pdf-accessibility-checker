# WCAG 2.1 Level A & AA Coverage Taxonomy

> **Executive Summary**: This document provides a complete, structured taxonomy of all 50 Success Criteria in WCAG 2.1 Level A and Level AA. It maps each criterion to its current project categorization: **Implemented**, **Planned (Deterministic Milestone)**, **AI-Assisted Evaluation Candidate**, **Unassigned in Scope**, **Explicitly Out of Scope**, or **Not Applicable**.

---

## 1. Taxonomy Summary & Status Distribution

| Status Category | Count | Definition |
|---|:---:|---|
| **Implemented** | 5 | Fully operational rule-based checks in the current screening engine ([`core/checks.py`](../core/checks.py)). |
| **Planned (Deterministic)** | 15 | Programmatic and structural heuristics assigned to active or upcoming milestones (Milestones 5–7). |
| **AI-Assisted Candidate** | 7 | Heuristics that cannot be settled deterministically, designated for cloud AI/vision model heuristic evaluation (Milestone 8 & beyond). |
| **Unassigned in Scope** | 5 | Deterministic checks within project domain (PDF or web documents), not yet assigned to an active milestone. |
| **Explicitly Out of Scope** | 8 | Strictly out of scope: requires live transactional backends, full site-wide multi-page architectures, or format-incompatible rendering engines. |
| **Not Applicable** | 10 | Media formats (prerecorded audio/video, live broadcasts, hardware motion sensors) absent from static PDFs or target pages. |
| **TOTAL** | **50** | **All WCAG 2.1 Level A (30) and Level AA (20) Success Criteria.** |

---

## 2. Principle 1: Perceivable

### Guideline 1.1: Text Alternatives
| Criterion | Level | Status | Target / Milestone | Evaluation Strategy & Scope Rationale |
|---|---|---|---|---|
| **1.1.1 Non-text Content** | A | **Implemented** / **AI-Assisted Candidate** | Implemented (Detection) & Milestone 8 (AI Heuristic) | Programmatic engine detects image resources (`check_page_images`). Evaluating alt-text accuracy, meaningful descriptions, or decorative status requires multimodal cloud AI vision models. |

### Guideline 1.2: Time-based Media
| Criterion | Level | Status | Target / Milestone | Evaluation Strategy & Scope Rationale |
|---|---|---|---|---|
| **1.2.1 Audio-only and Video-only (Prerecorded)** | A | **Not Applicable** | N/A | Static PDF documents and text screening prototypes do not host standalone prerecorded audio/video tracks. |
| **1.2.2 Captions (Prerecorded)** | A | **Not Applicable** | N/A | Prerecorded synchronized multimedia is outside the document domain. |
| **1.2.3 Audio Description or Media Alternative** | A | **Not Applicable** | N/A | Synchronized video tracks with visual narration are not within document scope. |
| **1.2.4 Captions (Live)** | AA | **Not Applicable** | N/A | Live broadcast media is not present in PDF documents or target prototype pages. |
| **1.2.5 Audio Description (Prerecorded)** | AA | **Not Applicable** | N/A | Prerecorded video narration is not within document scope. |

### Guideline 1.3: Adaptable
| Criterion | Level | Status | Target / Milestone | Evaluation Strategy & Scope Rationale |
|---|---|---|---|---|
| **1.3.1 Info and Relationships** | A | **Implemented** / **Planned** | Implemented (`check_structure`) & Milestone 6 | Validates `/StructTreeRoot` existence. Milestone 6 plans deterministic structural traversal (headings `<H1>`–`<H6>`, table headers `<TH>`/`<TD>`, lists `<L>`). |
| **1.3.2 Meaningful Sequence** | A | **Planned (Deterministic)** | Milestone 6 | Deterministically analyzes whether structural element `/K` sequence conforms to logical reading order across columns. |
| **1.3.3 Sensory Characteristics** | A | **AI-Assisted Candidate** | Milestone 8 (AI Heuristic) | Evaluating whether instructions rely solely on sensory visual cues ("click the green round button on the right") cannot be settled programmatically; designated for natural language AI assessment. |
| **1.3.4 Orientation** | AA | **Unassigned in Scope** | PDF / Web Candidate | Deterministically inspectable via PDF viewer rotation preferences or CSS `@media (orientation)` rules. |
| **1.3.5 Identify Input Purpose** | AA | **Planned (Deterministic)** | Milestone 5 | Deterministically checks HTML `autocomplete` attributes on common form inputs and PDF interactive form field flags. |

### Guideline 1.4: Distinguishable
| Criterion | Level | Status | Target / Milestone | Evaluation Strategy & Scope Rationale |
|---|---|---|---|---|
| **1.4.1 Use of Color** | A | **AI-Assisted Candidate** | Milestone 8 (AI Heuristic) | Determining whether color is the sole conveyor of information (e.g. in charts, graphs, or required fields) requires multimodal AI vision analysis to evaluate whether secondary cues exist. |
| **1.4.2 Audio Control** | A | **Not Applicable** | N/A | Static PDFs do not auto-play sound tracks longer than 3 seconds. |
| **1.4.3 Contrast (Minimum)** | AA | **Planned (Deterministic)** | Milestone 7 | Programmatically calculates foreground/background pixel luminosity ratio (4.5:1 normal text, 3:1 large text). |
| **1.4.4 Resize Text** | AA | **Unassigned in Scope** | PDF / Web Candidate | Programmatically checks HTML `meta viewport` settings to ensure user zoom is not disabled; verifies PDF vector text scaling. |
| **1.4.5 Images of Text** | AA | **Implemented** | Implemented (`check_page_text`) | Deterministically checks for extractable digital character streams to flag scanned bitmaps/images of text. |
| **1.4.10 Reflow** | AA | **Explicitly Out of Scope** | Out of Scope | Fixed-layout PDF specifications (ISO 32000-1) do not support responsive reflow; PDF/UA reflow requires proprietary reader support. |
| **1.4.11 Non-text Contrast** | AA | **Planned (Deterministic)** | Milestone 7 | Programmatically checks 3:1 contrast ratio for user interface components and graphical objects. |
| **1.4.12 Text Spacing** | AA | **Explicitly Out of Scope** | Out of Scope | PDF glyph positions are stored with absolute spatial coordinates; client-side spacing overrides cannot be tested statically without a live reflow rendering engine. |
| **1.4.13 Content on Hover or Focus** | AA | **Planned (Deterministic)** | Milestone 5 | Programmatically inspects CSS `:hover` / `:focus` tooltip dismissal and persistence in web page DOM scanning. |

---

## 3. Principle 2: Operable

### Guideline 2.1: Keyboard Accessible
| Criterion | Level | Status | Target / Milestone | Evaluation Strategy & Scope Rationale |
|---|---|---|---|---|
| **2.1.1 Keyboard** | A | **Planned (Deterministic)** | Milestone 5 | Programmatically evaluates focusability and keyboard event handlers on interactive HTML elements. |
| **2.1.2 No Keyboard Trap** | A | **Planned (Deterministic)** | Milestone 5 | Deterministically detects focus traps in interactive web dialogs, modals, and embedded scripts. |
| **2.1.4 Character Key Shortcuts** | A | **Planned (Deterministic)** | Milestone 5 | Deterministically detects single-character shortcut keys lacking mechanisms to remap or disable them in web applications. |

### Guideline 2.2: Enough Time
| Criterion | Level | Status | Target / Milestone | Evaluation Strategy & Scope Rationale |
|---|---|---|---|---|
| **2.2.1 Timing Adjustable** | A | **Not Applicable** | N/A | Static PDF documents do not impose session expiration timeouts or time limits. |
| **2.2.2 Pause, Stop, Hide** | A | **Planned (Deterministic)** | Milestone 5 | Programmatically inspects web pages for auto-advancing carousels, tickers, and unpausable animations. |

### Guideline 2.3: Seizures and Physical Reactions
| Criterion | Level | Status | Target / Milestone | Evaluation Strategy & Scope Rationale |
|---|---|---|---|---|
| **2.3.1 Three Flashes or Below Threshold** | A | **Not Applicable** | N/A | Static PDFs and standard document content do not feature strobing or flashing light sequences. |

### Guideline 2.4: Navigable
| Criterion | Level | Status | Target / Milestone | Evaluation Strategy & Scope Rationale |
|---|---|---|---|---|
| **2.4.1 Bypass Blocks** | A | **Planned (Deterministic)** | Milestone 5 | Deterministically validates skip-navigation links in web pages; in PDFs, verifies bookmark catalog dictionaries (`/Outlines`). |
| **2.4.2 Page Titled** | A | **Implemented** / **AI-Assisted Candidate** | Implemented (`check_title`) & Milestone 8 (AI Heuristic) | Deterministic check validates title metadata existence (`check_title`). Assessing whether the title is meaningful and descriptive given document contents is an AI language model task. |
| **2.4.3 Focus Order** | A | **Planned (Deterministic)** | Milestone 6 | Deterministically verifies PDF catalog `/Tabs` key (`/S` for structure order) and HTML DOM sequence. |
| **2.4.4 Link Purpose (In Context)** | A | **AI-Assisted Candidate** | Milestone 8 (AI Heuristic) | Flagging ambiguous link text (e.g. "click here") can be done via regex, but evaluating whether surrounding sentence/paragraph context makes the destination meaningful requires AI semantic analysis. |
| **2.4.5 Multiple Ways** | AA | **Explicitly Out of Scope** | Out of Scope | Single-document/page screener cannot evaluate site-wide navigation architectures (sitemaps vs search engines across a full domain). |
| **2.4.6 Headings and Labels** | AA | **Planned** / **AI-Assisted Candidate** | Milestone 6 & Milestone 8 (AI Heuristic) | Milestone 6 deterministically verifies tag structure and existence. Evaluating whether heading and label phrasing is *descriptive* and *clear* requires AI semantic language assessment. |
| **2.4.7 Focus Visible** | AA | **Planned (Deterministic)** | Milestone 5 | Programmatically inspects CSS `outline` / `box-shadow` rules to ensure focus indicators are not disabled (`outline: none`). |

### Guideline 2.5: Input Modalities
| Criterion | Level | Status | Target / Milestone | Evaluation Strategy & Scope Rationale |
|---|---|---|---|---|
| **2.5.1 Pointer Gestures** | A | **Planned (Deterministic)** | Milestone 5 | Programmatically flags multipoint or path-based gesture requirements in web application scripts. |
| **2.5.2 Pointer Cancellation** | A | **Explicitly Out of Scope** | Out of Scope | Verifying that mouse/touch down-events do not trigger irreversible actions requires dynamic event execution and runtime simulation. |
| **2.5.3 Label in Name** | A | **Planned (Deterministic)** | Milestone 5 | Deterministically checks that accessible name (`aria-label`) contains visible label text in interactive controls. |
| **2.5.4 Motion Actuation** | A | **Not Applicable** | N/A | Accelerometer and device tilt triggers are not utilized in static documents or target pages. |

---

## 4. Principle 3: Understandable

### Guideline 3.1: Readable
| Criterion | Level | Status | Target / Milestone | Evaluation Strategy & Scope Rationale |
|---|---|---|---|---|
| **3.1.1 Language of Page** | A | **Implemented** / **Planned** | Implemented (`check_language`) & Milestone 5 | Deterministically evaluates PDF catalog `/Lang` dictionary; Milestone 5 evaluates `<html lang="...">` on web pages. |
| **3.1.2 Language of Parts** | AA | **Unassigned in Scope** | PDF / Web Candidate | Deterministically inspects inline structure span `/Lang` tags in PDF structure trees or nested HTML `lang` attributes. |

### Guideline 3.2: Predictable
| Criterion | Level | Status | Target / Milestone | Evaluation Strategy & Scope Rationale |
|---|---|---|---|---|
| **3.2.1 On Focus** | A | **Planned (Deterministic)** | Milestone 5 | Programmatically detects automated context changes (e.g. form submission, page redirects) triggered solely on focus. |
| **3.2.2 On Input** | A | **Planned (Deterministic)** | Milestone 5 | Programmatically detects automatic page submits or context shifts triggered by changing form control inputs. |
| **3.2.3 Consistent Navigation** | AA | **Explicitly Out of Scope** | Out of Scope | Requires multi-page site comparison across distinct pages; cannot be evaluated on an isolated document. |
| **3.2.4 Consistent Identification** | AA | **Explicitly Out of Scope** | Out of Scope | Requires comparing icons and functional components across multiple distinct web pages. |

### Guideline 3.3: Input Assistance
| Criterion | Level | Status | Target / Milestone | Evaluation Strategy & Scope Rationale |
|---|---|---|---|---|
| **3.3.1 Error Identification** | A | **Explicitly Out of Scope** | Out of Scope | Requires submitting invalid form data dynamically to observe assistive error messaging from a live server. |
| **3.3.2 Labels or Instructions** | A | **Planned (Deterministic)** | Milestone 5 & Unassigned | Programmatically inspects `<label>` associations in HTML forms and `/TU` tooltip strings in PDF interactive forms. |
| **3.3.3 Error Suggestion** | AA | **AI-Assisted Candidate** | Milestone 8 (AI Heuristic) | Evaluating whether automated error messages offer constructive, context-aware suggestions for correction requires semantic AI reasoning. |
| **3.3.4 Error Prevention (Legal, Financial, Data)** | AA | **Explicitly Out of Scope** | Out of Scope | Requires domain-specific business logic awareness to detect financial or legal transaction commitments. |

---

## 5. Principle 4: Robust

### Guideline 4.1: Compatible
| Criterion | Level | Status | Target / Milestone | Evaluation Strategy & Scope Rationale |
|---|---|---|---|---|
| **4.1.1 Parsing** | A | **Planned (Deterministic)** | Milestone 5 | Deterministically validates HTML markup syntax (duplicate attributes, proper nesting, unique IDs). *(Obsoleted in WCAG 2.2, retained in 2.1)*. |
| **4.1.2 Name, Role, Value** | A | **Planned (Deterministic)** | Milestone 5 & Milestone 6 | Deterministically verifies accessible names, ARIA roles, and state values for custom HTML widgets and PDF interactive form controls. |
| **4.1.3 Status Messages** | AA | **Planned (Deterministic)** | Milestone 5 | Programmatically checks for `role="status"`, `role="alert"`, or `aria-live` regions for asynchronous updates in web scanning. |
