# Requirement Traceability Matrix

Generated from `docs/docdata.py` and the real test-result files in `tests/`. Architecture references (ARCH-n) and design references (DES-n) are defined in `docs/DESIGN.md`. ST-10 (the full demonstration script) is a system test for every FR and is therefore listed against all of them.

| Sl. No | Requirement ID | Brief Description of Requirement | Architecture Reference | Design Reference | Code File Reference | Test Case ID | System Test Case ID |
|---|---|---|---|---|---|---|---|
| 1 | FR-01 | Interactive prompt and read-eval loop | ARCH-1 Shell Core layer | DES-03, DES-06 | shell.c, parser.c | TC-47, UT-18 | ST-01, ST-02, ST-10 |
| 2 | FR-02 | Non-interactive input sources | ARCH-1 Shell Core layer | DES-01, DES-03 | main.c, shell.c | TC-50, TC-51, TC-62, TC-63, TC-76 | ST-10 |
| 3 | FR-03 | Tokenization and quoting | ARCH-2 Parser layer | DES-06, DES-07 | parser.c | TC-37, TC-39, TC-40, UT-01, UT-02, UT-05, UT-06 | ST-10 |
| 4 | FR-04 | Syntax error detection and reporting | ARCH-2 Parser layer | DES-06, DES-04 | parser.c, shell.c | TC-41, TC-42, TC-43, TC-44, TC-45, TC-46, TC-70, TC-73, UT-12, UT-13, UT-14, UT-15, UT-16, UT-22, UT-23 | ST-10 |
| 5 | FR-05 | External command execution with PATH search | ARCH-3 Executor layer | DES-09, DES-10 | executor.c | TC-02, TC-03, TC-10, TC-48, TC-49 | ST-02, ST-10 |
| 6 | FR-06 | Foreground wait and exit status | ARCH-3 Executor layer | DES-12 | executor.c | TC-30, TC-56 | ST-04, ST-10 |
| 7 | FR-07 | Invalid command handling | ARCH-3 Executor layer | DES-10 | executor.c | TC-08, TC-09, TC-66 | ST-10 |
| 8 | FR-08 | Built-in cd | ARCH-4 Built-in Command layer | DES-14, DES-15 | builtins.c | TC-04, TC-05, TC-06, TC-07, TC-65 | ST-10 |
| 9 | FR-09 | Built-in pwd | ARCH-4 Built-in Command layer | DES-14, DES-16 | builtins.c | TC-01 | ST-10 |
| 10 | FR-10 | Built-in exit | ARCH-4 Built-in Command layer | DES-14, DES-17 | builtins.c | TC-31, TC-32, TC-33, TC-53 | ST-09, ST-10 |
| 11 | FR-11 | Built-in help | ARCH-4 Built-in Command layer | DES-14, DES-18 | builtins.c | TC-34 | ST-10 |
| 12 | FR-12 | Environment variables | ARCH-4 Built-in Command layer | DES-19, DES-20 | builtins.c, executor.c, utils.c | TC-23, TC-24, TC-25, TC-26, TC-27, TC-64, UT-19 | ST-10 |
| 13 | FR-13 | Variable and tilde expansion | ARCH-2 Parser layer | DES-08 | parser.c | TC-28, TC-29, TC-38, TC-60, TC-61, TC-72, UT-03, UT-04, UT-17, UT-20, UT-21 | ST-10 |
| 14 | FR-14 | Output redirection > | ARCH-3 Executor layer | DES-11 | executor.c | TC-12, TC-13, TC-22, TC-71, UT-08, UT-24 | ST-10 |
| 15 | FR-15 | Append redirection >> | ARCH-3 Executor layer | DES-11 | executor.c | TC-14, TC-15, UT-09 | ST-10 |
| 16 | FR-16 | Input redirection < | ARCH-3 Executor layer | DES-11 | executor.c | TC-11 | ST-10 |
| 17 | FR-17 | Redirection error handling | ARCH-3 Executor layer | DES-11, DES-10 | executor.c | TC-16, TC-17 | ST-10 |
| 18 | FR-18 | Pipelines | ARCH-3 Executor layer | DES-09, DES-10 | executor.c | TC-18, TC-19, TC-20, TC-21, TC-57, TC-58, UT-07 | ST-10 |
| 19 | FR-19 | Command sequencing with ; | ARCH-1 Shell Core layer | DES-04, DES-06 | shell.c, parser.c | TC-35, UT-11 | ST-10 |
| 20 | FR-20 | Background execution with & | ARCH-3 Executor layer | DES-09, DES-13 | executor.c | TC-36, TC-74, TC-75, UT-10 | ST-05, ST-07, ST-10, ST-11 |
| 21 | FR-21 | Signal handling | ARCH-6 Signal / OS interface | DES-05, DES-10, DES-12 | shell.c, executor.c |  | ST-03, ST-04, ST-07, ST-08, ST-10, ST-11 |
| 22 | FR-22 | Graceful termination | ARCH-1 Shell Core layer | DES-03, DES-17, DES-02 | shell.c, builtins.c | TC-52 | ST-06, ST-10 |
| 23 | NFR-01 | Performance | ARCH-3 | DES-09 | executor.c | NF-01, NF-02, NF-03 | - |
| 24 | NFR-02 | Robustness | ARCH-2, ARCH-3 | DES-06, DES-09 | parser.c, executor.c | SC-12, SC-13, TC-54, TC-55, TC-57, TC-77 | ST-12 |
| 25 | NFR-03 | Usability | ARCH-1, ARCH-4 | DES-03, DES-18 | shell.c, builtins.c | NF-04, NF-08, TC-34 | ST-01 |
| 26 | NFR-04 | Maintainability | ARCH-1..ARCH-5 | all | all modules, Makefile | NF-05 | - |
| 27 | NFR-05 | Portability | ARCH-6 | DES-05, DES-09 | all (POSIX interfaces) | NF-06 | - |
| 28 | NFR-06 | Security | ARCH-3 | DES-10 | executor.c | SC-01, SC-02, SC-03, SC-04, SC-05, SC-06, SC-07, SC-08, SC-09, SC-10, SC-11, SC-12, SC-13 | ST-03, ST-04, ST-08, ST-12 |
| 29 | NFR-07 | Testability | ARCH-1, ARCH-2 | DES-01, DES-06 | main.c, parser.c | TC-50, TC-51, TC-62 | - |
| 30 | NFR-08 | Memory safety and resource management | ARCH-2, ARCH-3, ARCH-5 | DES-09, DES-21 | parser.c, executor.c, utils.c | SC-09, TC-77 | ST-12 |
| 31 | NFR-09 | Reliability | ARCH-1, ARCH-3 | DES-04, DES-10 | shell.c, executor.c | NF-07, TC-05, TC-08, TC-16, TC-17, TC-41 | ST-03 |
| 32 | SR-01 | The shell shall pass every word to an executed program only as one element of the argv vector given to execvp() (SO-1) | ARCH-2, ARCH-3 | DES-07, DES-09, DES-10 | parser.c, executor.c | SC-01, SC-03, SC-04 | - |
| 33 | SR-02 | Text produced by expansion ($NAME, ${NAME}, $?, $$, ~) shall not be scanned again for operators, quotes or further expansions: a variable whose value is 'a; echo pwned' shall be passed as the single argument 'a; echo pwned' (SO-1) | ARCH-2 | DES-07, DES-08 | parser.c | SC-02 | - |
| 34 | SR-03 | The shell shall not call setuid, setgid, seteuid, setegid, setreuid or setresuid, and every executed program shall run with the same user and group ids as the shell (SO-2) | ARCH-3 | DES-10 | executor.c | SC-05 | - |
| 35 | SR-04 | The shell shall not create any file on its own initiative (no history, log or state file); the only files it creates are those named by the user in > or >> redirections (SO-3) | ARCH-1, ARCH-3 | DES-03, DES-11 | shell.c, executor.c | SC-06 | - |
| 36 | SR-05 | Files created by > or >> shall be created with mode 0644 modified by the process umask, so the resulting permissions are never more permissive than 0644 (for example 0600 under umask 077) (SO-3) | ARCH-3 | DES-11 | executor.c | SC-07 | - |
| 37 | SR-06 | The parser and executor shall handle every input line without memory errors and without fixed-size buffers for user input; a fuzz run of 200000 random inputs in the parser and 600 random command lines in the real shell shall give 0 crashes, hangs or sanitizer reports (SO-4) | ARCH-2, ARCH-5 | DES-06, DES-07, DES-21 | parser.c, utils.c | SC-12, SC-13 | ST-12 |
| 38 | SR-07 | Environment variable names accepted by export, unset and NAME=VALUE shall match [A-Za-z_][A-Za-z0-9_]*; any other name shall be rejected with status 1 and an error message, leaving the environment unchanged (SO-4) | ARCH-4 | DES-19, DES-20, DES-21 | builtins.c, executor.c, utils.c | SC-08 | - |
| 39 | SR-08 | Executed programs shall inherit no open file descriptor other than 0, 1 and 2: pipe ends and redirection descriptors shall be closed in every child and the script file descriptor shall be close-on-exec (SO-5) | ARCH-1, ARCH-3 | DES-01, DES-09, DES-11 | main.c, executor.c | SC-09, SC-10 | - |
| 40 | SR-09 | The shell shall keep running when SIGINT or SIGTSTP (Ctrl+C, Ctrl+Z) is delivered at the prompt or during a foreground job, and the SIGINT handler shall only set a flag (async-signal-safe) (SO-5) | ARCH-6 | DES-05, DES-12 | shell.c, executor.c | - | ST-03, ST-04, ST-08 |
| 41 | SR-10 | A background job shall not read from the shell's standard input unless the user redirects it: its standard input shall be /dev/null (SO-5) | ARCH-3 | DES-10 | executor.c | SC-11 | - |
