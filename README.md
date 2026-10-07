# mysh — Simple Shell (Command Line Interpreter): Project Documentation

Documentation for **Mini Project 15 — Simple Shell (Command Line Interpreter)**, built for **UE24CS341A: Software Engineering** at PES University, Bangalore (Department of Computer Science & Engineering, Section F).

`mysh` is a Unix-like command-line interpreter written in C (C11) using only POSIX system calls. This repository contains the **software engineering documents** for the project: the requirements specification, the architecture and design specification, and the test plan. It does **not** contain the source code.

---

## Table of Contents

- [Repository Contents](#repository-contents)
- [Project Overview](#project-overview)
- [Document Summaries](#document-summaries)
- [Architecture at a Glance](#architecture-at-a-glance)
- [Requirements at a Glance](#requirements-at-a-glance)
- [Security](#security)
- [Test Results Summary](#test-results-summary)
- [Traceability](#traceability)
- [Scope and Known Limitations](#scope-and-known-limitations)
- [How to Read These Documents](#how-to-read-these-documents)
- [Team](#team)
- [References](#references)

---

## Repository Contents

| File | Document | Version |
|------|----------|---------|
| `Software_Requirement_Specification_SRS.pdf` | Software Requirements Specification (SRS) | v1.0 (2026-10-01) |
| `Software_Architecture_Design_SAD.pdf` | Software Architecture and Design Specification (SAD) | v1.0, Draft (2026-10-03) |
| `Software_Test_Plan_STP.pdf` | Software Test Plan (STP) | v1.0, Draft, Part-1 submission |

## Project Overview

`mysh` reads a line of text, interprets it and asks the operating system to run the requested programs. The purpose of the project is to demonstrate the core mechanisms of a Unix shell (process creation, execution, waiting, descriptors and signals) in a well-structured, tested C code base.

**Planned and documented features**

- Interactive prompt and read-eval loop (`mysh:<current directory>$`)
- Non-interactive input: script files, `-c "command"` strings and piped stdin
- External program execution with `PATH` search and exit-status tracking (`$?`)
- Quoting (`'single'`, `"double"`, `\escape`) and `#` comments, with syntax-error reporting
- Variable and tilde expansion: `$NAME`, `${NAME}`, `$?`, `$$`, `~`
- Built-ins: `cd`, `pwd`, `exit`, `help`, `export`, `unset`, `env`
- Redirection (`<`, `>`, `>>`), pipelines (`|`), sequencing (`;`)
- Background execution with `&` and `[id]+ Done` completion notices
- Signal handling: Ctrl+C interrupts the line or foreground job without killing the shell; Ctrl+D exits

**Command-line interface (as specified)**

```text
mysh                  interactive if stdin is a terminal, otherwise reads stdin silently
mysh -c "cmd"         execute a command string and exit
mysh script_file      execute a script file
mysh --help           print usage
mysh --version        print version
```

**Command grammar**

```text
line     := pipeline { (';' | '&' | newline) pipeline } [ '&' ]
pipeline := command { '|' command }
command  := { WORD | redirect }          (at least one WORD)
redirect := '<' WORD | '>' WORD | '>>' WORD
WORD     := unquoted text | 'single quoted' | "double quoted" | \char
comment  := '#' ... end of line          (only where a word could start)
```

**Exit status codes**

| Code    | Meaning                                                      |
|---------|--------------------------------------------------------------|
| `0`     | Success                                                      |
| `1`     | General failure (built-in error, redirection, fork/pipe)     |
| `2`     | Syntax error, usage error, `exit` with non-numeric argument  |
| `126`   | Command found but cannot be executed                         |
| `127`   | Command (or script file) not found                           |
| `128+N` | Terminated by signal N (`130` = SIGINT, `137` = SIGKILL)     |

## Document Summaries

### Software Requirements Specification (SRS)

Defines *what* mysh must do. Contents:

1. Introduction, product perspective, user classes, operating environment and constraints
2. External interfaces (user interface, OS/POSIX interfaces, no network or hardware interfaces)
3. Analysis models: UML use-case diagram (UC1–UC12), lifecycle and execution flowcharts, sequence diagram, data-flow diagram, error-handling flow, component diagram
4. System features with **22 functional requirements (FR-01 – FR-22)**
5. Non-functional requirements: performance, safety, **security objectives SO-1 – SO-5 and requirements SR-01 – SR-10**, and **quality attributes NFR-01 – NFR-09**
6. Business rules, glossary, command grammar, data structures, status codes
7. **Appendix C: Requirement Traceability Matrix (RTM)**

### Software Architecture and Design Specification (SAD)

Defines *how* mysh is structured. Contents:

1. Goals, constraints and stakeholder concerns
2. UML component diagram and descriptions of six components (ARCH-1 – ARCH-6)
3. Chosen pattern (layered read-eval loop with pipes-and-filters), rejected alternatives and six architecture decision records (ADR-1 – ADR-6)
4. Risks and mitigations, and requirement-to-architecture traceability
5. **Security architecture:** trust zones and a STRIDE threat model
6. Design: lifecycle and execution flowcharts, key data structures, four UML sequence diagrams (SD-1 – SD-4), API definitions for five components, error handling, UX design, open issues
7. Design reference index (DES-01 – DES-21)

### Software Test Plan (STP)

Defines *how* mysh is verified. Contents:

1. Test items, features to be tested / not tested, strategy (unit, integration, system, acceptance) and entry/exit criteria
2. Security validation activities, test environment, schedule, deliverables, roles and risks
3. Traceability from every requirement to test cases
4. Test metrics, summary report and defect log
5. **Appendix A:** full specifications of 19 key test cases
6. **Appendix B:** catalogue of all 130 test cases with commands, expected output and results

## Architecture at a Glance

mysh uses a **layered, interpreter-style (read-eval loop) architecture** with **pipes-and-filters** at run time. Each layer has one reason to change: the parser knows nothing about processes, and the executor knows nothing about quoting.

| ID     | Component              | Source files (as designed)      | Responsibility                                                                |
|--------|------------------------|---------------------------------|-------------------------------------------------------------------------------|
| ARCH-1 | Shell Core             | `main.c`, `shell.c/h`           | Entry point, options, prompt, read-eval loop, signal policy, shell state      |
| ARCH-2 | Parser                 | `parser.c/h`                    | Tokenizing, quoting, expansion, syntax errors, builds `Pipeline` structures   |
| ARCH-3 | Executor               | `executor.c/h`                  | `fork`/`exec`, pipe wiring, redirection, wait/status mapping, background jobs |
| ARCH-4 | Built-in Commands      | `builtins.c/h`                  | Table-driven `cd`, `pwd`, `exit`, `help`, `export`, `unset`, `env`            |
| ARCH-5 | Utilities              | `utils.c/h`                     | Safe allocation, error reporting, growable string buffer, name validation     |
| ARCH-6 | OS interface / signals | (within `shell.c`, `executor.c`)| POSIX calls and signal dispositions                                           |

**Key design decisions (ADRs)**

| ADR   | Decision |
|-------|----------|
| ADR-1 | Parse and execute one pipeline at a time (so `export X=1; echo $X` works without a full syntax tree) |
| ADR-2 | A lone built-in runs in the shell process; built-ins in pipelines or with `&` run in a child |
| ADR-3 | The `SIGINT` handler only sets a flag and is installed without `SA_RESTART` |
| ADR-4 | Ignore `SIGTSTP`/`SIGQUIT` in the interactive shell (no job control) |
| ADR-5 | Expanded text is never re-tokenized (no field splitting), closing a class of injection bugs |
| ADR-6 | Every shell variable is an environment variable |

## Requirements at a Glance

| Category | IDs | Examples |
|----------|-----|----------|
| Functional | FR-01 – FR-22 | Prompt and loop, tokenization, syntax errors, PATH execution, built-ins, expansion, redirection, pipelines, `;`, `&`, signals, graceful termination |
| Performance | NFR-01 | Background start returns within 500 ms; 1000 external commands in ≤ 5 s; 1000 built-ins in ≤ 1 s |
| Robustness | NFR-02 | 100,000-character argument, 2,000 arguments, 10-stage pipeline, 300 consecutive pipelines, 200,000 fuzzed lines |
| Usability | NFR-03 | All diagnostics on stderr as `mysh: ...`; `help` ≤ 25 lines of ≤ 80 characters |
| Maintainability | NFR-04 | Zero warnings under `-std=c11 -Wall -Wextra -Wpedantic -Werror`; adding a built-in needs one table entry and one function |
| Portability | NFR-05 | Compiles as C11 and as C99 + POSIX.1-2008 |
| Security | NFR-06 / SR-01 – SR-10 | See [Security](#security) |
| Testability | NFR-07 | Every FR has an automated terminal-free test; whole suite runs with `make test` |
| Memory safety | NFR-08 | Zero ASan/UBSan/LSan reports; no leaked descriptors after 300 pipelines |
| Reliability | NFR-09 | None of 10 kinds of user error terminates the shell |

## Security

Five security objectives, each backed by verifiable requirements and tests:

| Objective | Summary | Key requirements |
|-----------|---------|------------------|
| SO-1 | Prevent command and argument injection | SR-01 (argv-only `execvp()`, no `system()`/`popen()`/`sh -c`), SR-02 (no re-scan of expanded text) |
| SO-2 | Prevent privilege escalation | SR-03 (no `setuid`-family calls) |
| SO-3 | Protect user data from unintended disclosure | SR-04 (no history/log/state files), SR-05 (files created with `0644 & ~umask`) |
| SO-4 | Memory safety and robustness against hostile input | SR-06 (no fixed-size buffers, fuzzing), SR-07 (strict variable-name validation) |
| SO-5 | Prevent resource leakage and loss of control | SR-08 (only fds 0–2 inherited), SR-09 (Ctrl+C/Ctrl+Z cannot kill or freeze the shell), SR-10 (`/dev/null` stdin for background jobs) |

The SAD (section 3.9) contains a trust-zone diagram and a STRIDE threat model covering spoofing, tampering, repudiation, information disclosure, denial of service and elevation of privilege.

## Test Results Summary

As reported in the STP (execution of 2026-10-03, Ubuntu 24.04.4, gcc 13.3.0):

| Category | Prefix | Designed | Passed | Failed |
|----------|--------|---------:|-------:|-------:|
| Unit | `UT` | 24 | 24 | 0 |
| Functional / integration / negative / robustness | `TC` | 73 | 73 | 0 |
| Security | `SC` | 13 | 13 | 0 |
| Non-functional | `NF` | 8 | 8 | 0 |
| System (pseudo-terminal) | `ST` | 12 | 12 | 0 |
| **Total** | | **130** | **130** | **0** |

- **Requirement coverage:** 22/22 functional, 9/9 non-functional, 10/10 security requirements
- **Defects:** 4 logged (1 product defect, 3 test defects), all closed in the same cycle; 0 open critical/high defects
  - The one product defect (D-3, Medium, SR-08): the script file descriptor was inherited by programs launched from a script; fixed by opening the script close-on-exec
- **Fuzzing:** 200,000 random lines through the parser and 600 random command lines through the real shell, with 0 crashes, hangs or sanitizer reports
- **Planned, not yet performed:** regression run on each member's machine (including as a non-root user), non-Linux POSIX verification, pty suite under sanitizers, coverage-guided fuzzing, third-party penetration test, acceptance demonstration

## Traceability

Every requirement is traced end to end:

```text
Requirement (SRS)  →  Architecture (ARCH-n)  →  Design (DES-n)  →  Source file  →  Test case (UT / TC / SC / NF / ST)
```

- Full matrix: **SRS Appendix C** (41 rows: FR, NFR and SR)
- Test-side view: **STP section 13**
- Architecture/design view: **SAD section 3.8** and the design reference index (SAD section 5.4)

**Test ID prefixes:** `UT` unit · `TC` functional/integration/negative/robustness · `SC` security · `NF` non-functional · `ST` system

## Scope and Known Limitations

Out of scope by design:

- Job control (`fg`, `bg`, `jobs`) and Ctrl+Z suspension
- Wildcard/glob expansion, command substitution, `&&`, `||`, here-documents, `2>` / `&>`, aliases, functions, control flow, `~user`
- Line editing, history and tab completion
- At most 64 background jobs are tracked; "Done" notices appear only at the next prompt
- Expanded variable text is not field-split (a deliberate, security-motivated deviation from POSIX)
- Tested only on Ubuntu 24.04

## How to Read These Documents

| If you want to... | Start with |
|-------------------|-----------|
| Understand what the shell does | SRS sections 1–3 and 5 |
| See the design and why it was chosen | SAD sections 3 and 4 |
| Check how a requirement is verified | SRS Appendix C, then STP Appendix B |
| Review the security approach | SAD section 3.9, SRS section 6.3, STP section 5.1 |
| See test evidence | STP sections 13–14 and Appendices A–B |

## Team

**Section F — Department of Computer Science & Engineering, PES University, Bangalore**

| Name                 | SRN           |
|----------------------|---------------|
| Kari Bhavitha        | PES1UG25CS821 |
| Pavana P             | PES1UG24CS320 |
| Prarthana Shivakumar | PES1UG24CS339 |
| Raghavendra H        | PES1UG24CS356 |

**Faculty guide:** Ashok Kumar Patil

## References

- The Open Group, *POSIX.1-2008 (IEEE Std 1003.1-2008)*: Shell Command Language and System Interfaces
- W. R. Stevens and S. A. Rago, *Advanced Programming in the UNIX Environment*, 3rd ed.
- IEEE Std 830-1998 (SRS), IEEE Std 1016-2009 (SDD), IEEE Std 829-2008 (test documentation), ISO/IEC/IEEE 42010:2011 (architecture description)
- OWASP Secure Coding Practices; SEI CERT C Coding Standard

---

*Original student work prepared for academic submission.*
