# Architecture and Design - Simple Shell (Command Line Interpreter)

Implementation language: C11 (POSIX.1-2008), binary name `mysh`. All statements below describe code that exists in `src/`.

## 1. Architecture overview

The shell is a single process organised as five cooperating modules on top of the POSIX system-call interface. The **Shell Core** owns the read-eval loop, the **Parser** converts text to a `Pipeline` data structure, the **Executor** turns a `Pipeline` into processes, the **Built-in** layer implements commands that must run inside the shell process, and **Utilities** provide shared helpers.

![Figure 1: System architecture](diagrams/01_architecture.png)

![Figure 2: UML component diagram](diagrams/02_components.png)

### Module decomposition and component responsibilities

| Module | Files | Responsibility | Depends on |
|---|---|---|---|
| Shell Core (ARCH-1) | main.c, shell.c, shell.h | Program entry and options; Shell state ($?, running flag, job table); read-eval loop; prompt; SIGINT policy; executes each parsed pipeline in turn | parser, executor, utils |
| Parser (ARCH-2) | parser.c, parser.h | Tokenizes one pipeline at a time; quoting, escapes, comments; $-expansion and ~; builds Command/Pipeline structures; syntax errors | utils |
| Executor (ARCH-3) | executor.c, executor.h | fork/exec, pipe wiring, redirection with dup2, waiting and status mapping, background job table and reaping, NAME=VALUE assignments, built-in dispatch (parent vs child) | builtins, parser types, shell state, utils |
| Built-ins (ARCH-4) | builtins.c, builtins.h | cd, pwd, exit, help, export, unset, env; table-driven dispatch | shell state, utils |
| Utilities (ARCH-5) | utils.c, utils.h | xmalloc/xrealloc/xstrdup, shell_error, StrBuf, name validation, trimming | - |
| OS interface (ARCH-6) | (system calls) | fork, execvp, pipe, dup2, open, waitpid, sigaction, chdir, getcwd, setenv/getenv | - |

## 2. Key data structures

| Structure | Defined in | Purpose |
|---|---|---|
| `Command` | parser.h | `argv[]`, `argc`, `infile`, `outfile`, `append` for one simple command |
| `Pipeline` | parser.h | array of `Command`, `ncmds`, `background` flag, source `text` |
| `Shell` | shell.h | `last_status` ($?), `running`, `exit_code`, `interactive`, background `Job` table (max 64) |
| `StrBuf` | utils.h | growable string used while building words |

## 3. Shell lifecycle and control flow

1. `main()` handles `-c`, script file, `--help`, `--version` (DES-01), then calls `shell_init()` (DES-02).
2. In interactive mode `shell_setup_signals()` installs the SIGINT handler (no `SA_RESTART`) and ignores SIGQUIT/SIGTSTP/SIGTTIN/SIGTTOU (DES-05).
3. `shell_run_stream()` loops: reap finished background jobs, print the prompt, `getline()`. EINTR means Ctrl+C (redraw prompt, `$?`=130); EOF means Ctrl+D (DES-03).
4. `shell_execute_line()` repeatedly calls `parse_next_pipeline()` and `execute_pipeline()` until the line is consumed. Parsing one pipeline at a time makes `export X=1; echo $X` work (DES-04).

![Figure 3: Shell lifecycle (high-level flowchart)](diagrams/03_lifecycle_flow.png)

## 4. Command parsing flow

`parse_next_pipeline()` (DES-06) skips blanks and comments, then reads tokens until an unquoted `;`, `&`, newline or end of input:

* `read_word()` (DES-07) builds a word character by character, handling `'...'`, `"..."`, backslash, `$` expansion (DES-08) and a leading `~`. An unquoted expansion that becomes empty is dropped.
* `|` finishes the current `Command` and starts the next; `<`, `>`, `>>` read the following word as the file name.
* On any violation (unterminated quote, missing file name, empty stage, `&&`, `||`, bad `${}`) the function frees what it built, moves the cursor to the end of the line and returns `PARSE_ERROR` with a message.

## 5. Process execution flow

`execute_pipeline()` (DES-09) first handles the cases that must not fork: a lone `NAME=VALUE` line (DES-20) and a lone built-in without `&` (run in the shell so `cd`, `exit` and `export` take effect; redirections are applied to fd 0/1 and restored afterwards). Otherwise it creates one child per command, connecting neighbours with `pipe()`. In each child (`exec_child`, DES-10) the signal policy is set, pipe ends are attached with `dup2`, redirections from the command override them (DES-11), then a built-in is run or `execvp()` is called. The parent closes unused pipe ends immediately, then either records a background job (DES-13) or waits for every child (DES-12).

![Figure 4: Command execution flowchart](diagrams/04_execution_flow.png)

![Figure 6: UML sequence diagram SD-1: foreground pipeline](diagrams/06_sequence.png)

## 6. Data flow

![Figure 7: Data-flow diagram, level 1](diagrams/07_dfd_level1.png)

## 7. Error-handling flow

Errors are reported with `shell_error()` (prefix `mysh: `) on stderr and never terminate the shell. Status codes follow common shell conventions: 1 general failure, 2 syntax error / usage, 126 found but not executable, 127 not found, 128+N killed by signal N, 130 interrupted at the prompt.

![Figure 8: Error-handling flow](diagrams/08_error_flow.png)

## 8. Use cases

![Figure 5: UML use-case diagram](diagrams/05_use_case.png)

## 9. Design decisions and rationale

| Decision | Rationale |
|---|---|
| Parse and execute one pipeline at a time | Correct `$VAR` semantics across `;` without a full command-list AST |
| Lone built-ins run in the shell process; built-ins in pipelines run in a child | `cd`/`exit`/`export` must change the shell itself; pipeline semantics need separate processes |
| SIGINT handler only sets a flag and has no `SA_RESTART` | Async-signal-safe; makes `getline()` return EINTR so the prompt can be redrawn |
| SIGTSTP/SIGQUIT ignored in the shell | No job control, so a stopped child could never be resumed; ignored signals are inherited across `exec` |
| Background children ignore SIGINT and read `/dev/null` | Ctrl+C must not kill background jobs; they must not steal terminal input |
| Reap background jobs with `waitpid(-1, WNOHANG)` before each prompt | No zombies accumulate; no signal handler complexity |
| `execvp()` with an argv vector, never `system()` | No second round of shell interpretation of user text |
| Shell variables are environment variables | Simpler model, always visible to children (documented limitation) |

## 10. Design reference index

| Design ref | Function / element | File |
|---|---|---|
| DES-01 | main() - option handling (-c, script, --help, --version) | main.c |
| DES-02 | shell_init() / shell_cleanup() - state and lifecycle | shell.c |
| DES-03 | shell_run_stream() - prompt, getline, EINTR and EOF handling | shell.c |
| DES-04 | shell_execute_line() - parse/execute loop over pipelines | shell.c |
| DES-05 | shell_setup_signals() and sigint_handler() | shell.c |
| DES-06 | parse_next_pipeline() - grammar, operators, syntax errors | parser.c |
| DES-07 | read_word() - quoting, escapes, comment handling | parser.c |
| DES-08 | expand_dollar() and tilde expansion | parser.c |
| DES-09 | execute_pipeline() - fork loop, pipe wiring, wait/background | executor.c |
| DES-10 | exec_child() - child setup, execvp, exec failure codes | executor.c |
| DES-11 | apply_redirections() - open/dup2 for <, >, >> | executor.c |
| DES-12 | wait_foreground() - waitpid and status mapping | executor.c |
| DES-13 | jobs_add() / jobs_reap() - background job table | executor.c |
| DES-14 | Built-in table, is_builtin(), run_builtin(), run_builtin_in_parent() | builtins.c, executor.c |
| DES-15 | bi_cd() | builtins.c |
| DES-16 | bi_pwd() | builtins.c |
| DES-17 | bi_exit() | builtins.c |
| DES-18 | bi_help() | builtins.c |
| DES-19 | bi_export(), bi_unset(), bi_env() | builtins.c |
| DES-20 | all_assignments() / run_assignments() - NAME=VALUE | executor.c |
| DES-21 | utils: StrBuf, xmalloc/xrealloc, shell_error, is_valid_name | utils.c |

| Architecture ref | Layer | Files | Figures |
|---|---|---|---|
| ARCH-1 | Shell Core layer | main.c, shell.c | Fig. 1, Fig. 3 |
| ARCH-2 | Parser layer | parser.c | Fig. 1, Fig. 2 |
| ARCH-3 | Executor layer | executor.c | Fig. 1, Fig. 4, Fig. 6 |
| ARCH-4 | Built-in Command layer | builtins.c | Fig. 1, Fig. 2 |
| ARCH-5 | Utility layer | utils.c | Fig. 1 |
| ARCH-6 | Signal / OS interface | shell.c, executor.c | Fig. 1, Fig. 8 |
