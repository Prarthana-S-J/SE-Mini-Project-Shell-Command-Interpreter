# Team Ownership and Plan of Work

> Member names: replace "Member 1..4" with the real names / SRNs when submitting. Ownership below is the documented division of the four functional areas of the shell.

## Product ownership

| Member | Primary Responsibility | Functional Features | Technical Contribution | Expected Deliverables |
|---|---|---|---|---|
| Member 1 | Shell core and process execution | FR-01, FR-02, FR-05, FR-06, FR-19, FR-22 | main.c; shell.c/h (state, read-eval loop, EINTR/EOF handling, shell_execute_line); executor.c: execute_pipeline() fork loop, wait_foreground() and exit-status mapping; option handling (-c, script). | Working prompt loop; execution of external commands with PATH lookup; $? maintained; graceful termination; -c/script/stdin modes. |
| Member 2 | Parser, expansion, built-ins and environment | FR-03, FR-08, FR-09, FR-12, FR-13 | parser.c/h: tokenizer, quoting, comments, Command/Pipeline structures, expand_dollar() and tilde; builtins.c/h: dispatch table, cd, pwd, export, unset, env; NAME=VALUE assignments. | Parser module with 24 unit tests; cd/pwd/export/unset/env; variable and tilde expansion. |
| Member 3 | Redirection, pipes, background jobs and signals | FR-14, FR-15, FR-16, FR-18, FR-20, FR-21 | executor.c: apply_redirections(), pipe wiring and descriptor hygiene in the fork loop, exec_child() signal/stdin setup, jobs_add()/jobs_reap(); shell.c: shell_setup_signals() and SIGINT handling. | <, >, >> for commands and built-ins; N-stage pipelines; background execution with Done notices; Ctrl+C/Ctrl+Z behaviour. |
| Member 4 | Error handling, exit/help built-ins, integration and verification | FR-04, FR-07, FR-10, FR-11, FR-17 | Syntax-error messages and recovery (parser.c error paths, shell.c status 2); exec failure codes 126/127 (exec_child); redirection-failure handling and fd restore for built-ins; bi_exit(), bi_help(); utils.c/h (StrBuf, xmalloc, shell_error, name validation); Makefile; unit, functional and pty test suites; sanitizer build; SRS/RTM. | Uniform error reporting; exit and help; utils module; Makefile; 24 unit + 74 functional + 10 terminal tests; ASan/UBSan run; requirements traceability. |

Every functional requirement has exactly one owning member (checked in `docs/CONSISTENCY_CHECK.md`):

| Requirement | Title | Owner |
|---|---|---|
| FR-01 | Interactive prompt and read-eval loop | Member 1 |
| FR-02 | Non-interactive input sources | Member 1 |
| FR-03 | Tokenization and quoting | Member 2 |
| FR-04 | Syntax error detection and reporting | Member 4 |
| FR-05 | External command execution with PATH search | Member 1 |
| FR-06 | Foreground wait and exit status | Member 1 |
| FR-07 | Invalid command handling | Member 4 |
| FR-08 | Built-in cd | Member 2 |
| FR-09 | Built-in pwd | Member 2 |
| FR-10 | Built-in exit | Member 4 |
| FR-11 | Built-in help | Member 4 |
| FR-12 | Environment variables | Member 2 |
| FR-13 | Variable and tilde expansion | Member 2 |
| FR-14 | Output redirection > | Member 3 |
| FR-15 | Append redirection >> | Member 3 |
| FR-16 | Input redirection < | Member 3 |
| FR-17 | Redirection error handling | Member 4 |
| FR-18 | Pipelines | Member 3 |
| FR-19 | Command sequencing with ; | Member 1 |
| FR-20 | Background execution with & | Member 3 |
| FR-21 | Signal handling | Member 3 |
| FR-22 | Graceful termination | Member 1 |

Shared modules: `executor.c` is shared by Members 1, 3 and 4 (fork/wait; redirection/pipes/jobs; exec failure codes); `parser.c` by Members 2 and 4 (tokenizer/expansion; syntax-error paths); `builtins.c` by Members 2 and 4 (cd/pwd/env; exit/help). All members review each other's changes at integration.

## Plan of work (6 weeks)

| Phase | Activities | Responsible member(s) | Expected deliverable | Functional features covered |
|---|---|---|---|---|
| Week 1 | Requirements analysis, architecture, project setup | All; Member 1 (architecture), Member 4 (SRS skeleton, Makefile) | Draft SRS, architecture and module diagram, repository layout, Makefile | Foundation for all FRs |
| Week 2 | Command parser and basic command execution | Member 2 (parser, tokenizer); Member 1 (prompt loop, fork/exec/wait) | parser.c/h, shell.c, executor.c skeleton; first runnable shell | FR-01, FR-03, FR-05, FR-06 |
| Week 3 | Built-ins, redirection and pipes | Member 2 (cd, pwd, env); Member 3 (redirection, pipes); Member 4 (exit, help) | builtins.c; apply_redirections(); N-stage pipeline | FR-08, FR-09, FR-10, FR-11, FR-12, FR-14..FR-16, FR-18 |
| Week 4 | Background jobs, signals, error handling and expansion | Member 3 (background, signals); Member 4 (error handling, syntax errors); Member 2 (expansion) | jobs table, SIGINT policy, 126/127 codes, syntax errors, $VAR expansion | FR-04, FR-07, FR-13, FR-17, FR-20, FR-21, FR-19 |
| Week 5 | Integration, testing and bug fixing | Member 4 (test suites, sanitizer); all members fix defects in their modules | Unit, functional and pty test suites; sanitizer run; defect fixes | All FRs verified; NFR-02, NFR-08 |
| Week 6 | Documentation, final testing and demonstration preparation | Member 4 (SRS, RTM); Member 1 (report); Members 2-3 (demo script, slides) | SRS, RTM, README, final report, slides, demo script | All |

## Notes

* The distinction between functional features and supporting activities (documentation, testing, slides) is respected: each member's primary contribution above is a set of functional requirements implemented in named modules.
* Testing, documentation and integration by Member 4 are additional to that member's functional ownership (FR-04, FR-07, FR-10, FR-11, FR-17).
