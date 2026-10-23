# Mini-Project Deliverables Part-1 - compliance checklist (ETA 07 Oct 2026)

Each line of `SE_Mini_Project_Delivereables_Part-1.pdf` and where it is satisfied.

| # | Deliverable item | Where | Status |
|---|---|---|---|
| 1 | SRS in the standard IEEE format (intro and other descriptive sections) | `docs/SRS.docx`, sections 1-3, 7, appendices (PES template structure, IEEE 830 content) | Done |
| 1.ii | FRs and NFRs, clear, unambiguous, concise, measurable | SRS section 5 (FR-01 to FR-22, each with behaviour and error behaviour) and 6.4 (NFR-01 to NFR-09 with numeric acceptance criteria) | Done |
| 1.iii | UML use-case diagram (at least 1) | SRS section 4 (Figure 5) and use-case table UC1-UC12 | Done |
| 1.iv | Security section with objectives and requirements (at least 2 each) | SRS 6.3: 5 objectives (SO-1..SO-5), 10 requirements (SR-01..SR-10), each verified by tests | Done |
| 2 | Test Plan in the standard IEEE format | `docs/STP.docx` - all 15 sections of the supplied template | Done |
| 2.ii | Sections 3, 4 and 5 filled | STP 3 Features to be tested, 4 Features not to be tested, 5 Strategy | Done |
| 2.iii | Section 5.1 security validation | STP 5.1 (static checks, injection, privilege, exposure, descriptors, signals, fuzzing, sanitizers) | Done |
| 2.iv | Traceability with the SRS | STP 3 and 13, SRS Appendix C, `docs/RTM.md` (FR, NFR and SR rows) | Done |
| 3 | Software Architecture and Design Specification in the standard format | `docs/SAD.docx` - follows the supplied SAD template (sections 1-5) | Done |
| 3.i.1 | Component diagram and description | SAD 3.3 (UML component diagram), 3.4 | Done |
| 3.i.2 | Architecture pattern | SAD 3.5 (layered / interpreter loop / pipes-and-filters, rejected alternatives, ADRs) | Done |
| 3.i.3 | Traceability to requirements | SAD 3.8 (FR, NFR, SR to components, design elements, files) | Done |
| 3.i.4 | Security architecture | SAD 3.9 (trust zones, STRIDE table, security design rules) | Done |
| 3.ii.1 | UML sequence diagrams (at least 2) | SAD 4.2: SD-1 pipeline, SD-2 background job, SD-3 Ctrl+C, SD-4 error paths | Done (4) |
| 3.ii.2 | API design | SAD 4.3 (parser, executor, built-ins, shell core, command-line interface, exit-status contract) | Done |
| 3.ii.3 | Error handling | SAD 4.4 (error classes, messages, statuses, flow diagram) | Done |
| 4 | Test cases update in the Test Plan, covering functional and non-functional requirements, at least 7-10 | STP Appendix A (full specifications of 19 cases) and Appendix B (all 130 executed tests: 24 unit, 94 functional/security/non-functional cases and 12 system) | Done |

Test status: All 130 designed tests were executed on 2026-10-03 (Ubuntu 24.04.4 LTS, Linux 6.18, gcc 13.3.0): 130 passed, 0 failed. All of these results come from automated runs; see `docs/STP.docx` section 14 and the files in `tests/`.
