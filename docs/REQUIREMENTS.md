# Requirements - Simple Shell (Command Line Interpreter)

Requirements describe the behaviour of the implemented shell `mysh` (source in `src/`). Every functional requirement has at least one executed test (see `docs/RTM.md`).

## Summary of functional requirements

| ID | Title | Feature | Priority | Owner |
|---|---|---|---|---|
| FR-01 | Interactive prompt and read-eval loop | Command Loop and Input Sources | High | Member 1 |
| FR-02 | Non-interactive input sources | Command Loop and Input Sources | High | Member 1 |
| FR-03 | Tokenization and quoting | Command-Line Parsing | High | Member 2 |
| FR-04 | Syntax error detection and reporting | Command-Line Parsing | High | Member 4 |
| FR-05 | External command execution with PATH search | External Command Execution | High | Member 1 |
| FR-06 | Foreground wait and exit status | External Command Execution | High | Member 1 |
| FR-07 | Invalid command handling | External Command Execution | High | Member 4 |
| FR-08 | Built-in cd | Built-in Commands | High | Member 2 |
| FR-09 | Built-in pwd | Built-in Commands | High | Member 2 |
| FR-10 | Built-in exit | Built-in Commands | High | Member 4 |
| FR-11 | Built-in help | Built-in Commands | Medium | Member 4 |
| FR-12 | Environment variables | Environment and Expansion | High | Member 2 |
| FR-13 | Variable and tilde expansion | Environment and Expansion | High | Member 2 |
| FR-14 | Output redirection > | I/O Redirection | High | Member 3 |
| FR-15 | Append redirection >> | I/O Redirection | High | Member 3 |
| FR-16 | Input redirection < | I/O Redirection | High | Member 3 |
| FR-17 | Redirection error handling | I/O Redirection | High | Member 4 |
| FR-18 | Pipelines | Pipelines and Sequencing | High | Member 3 |
| FR-19 | Command sequencing with ; | Pipelines and Sequencing | Medium | Member 1 |
| FR-20 | Background execution with & | Background Execution | High | Member 3 |
| FR-21 | Signal handling | Signal Handling | High | Member 3 |
| FR-22 | Graceful termination | Command Loop and Input Sources | High | Member 1 |

## Detailed functional requirements

### FR-01 - Interactive prompt and read-eval loop

| Field | Content |
|---|---|
| Requirement ID | FR-01 |
| Feature | Command Loop and Input Sources |
| Priority | High |
| Description | When standard input is a terminal the shell shall display a prompt containing the current working directory, read one line, execute it, and repeat until told to exit. |
| Expected system behaviour | Prompt has the form mysh:<cwd>$ and is written to stderr. Blank, whitespace-only and comment-only lines are accepted and do nothing (status unchanged). |
| Error / exception behaviour | If getcwd() fails the prompt falls back to mysh$ . A failed read caused by a signal redraws the prompt (see FR-21). |
| Owner (documented) | Member 1 |

### FR-02 - Non-interactive input sources

| Field | Content |
|---|---|
| Requirement ID | FR-02 |
| Feature | Command Loop and Input Sources |
| Priority | High |
| Description | The shell shall accept commands from (a) a terminal, (b) standard input when it is not a terminal, (c) a script file argument, and (d) a command string given with -c. --help and --version shall print information and exit. |
| Expected system behaviour | No prompt is printed and no job banners are shown in non-interactive modes. The exit status is the status of the last command, or the value given to exit. |
| Error / exception behaviour | -c without an argument prints a usage message and exits with status 2. An unreadable script file prints an error and exits with status 127. |
| Owner (documented) | Member 1 |

### FR-03 - Tokenization and quoting

| Field | Content |
|---|---|
| Requirement ID | FR-03 |
| Feature | Command-Line Parsing |
| Priority | High |
| Description | The parser shall split a line into words separated by blanks; single quotes shall preserve text literally, double quotes shall preserve blanks and operators but allow expansion, a backslash shall escape the next character, and text after an unquoted # at the start of a word shall be a comment. |
| Expected system behaviour | Operators \| < > >> ; & are recognised without surrounding spaces (echo x>f). Quoted operators are ordinary text. |
| Error / exception behaviour | Unterminated quotes are syntax errors (FR-04). |
| Owner (documented) | Member 2 |

### FR-04 - Syntax error detection and reporting

| Field | Content |
|---|---|
| Requirement ID | FR-04 |
| Feature | Command-Line Parsing |
| Priority | High |
| Description | The parser shall detect and report: unterminated single or double quotes, a redirection operator with no file name, an empty pipeline stage (leading, trailing or doubled \|), a redirection with no command, a malformed ${...}, and the unsupported operators && and \|\|. |
| Expected system behaviour | A message of the form 'mysh: <reason>' is written to stderr, $? is set to 2, and the remainder of the input line is discarded. The shell continues with the next line. |
| Error / exception behaviour | No command from the faulty pipeline is executed. The shell never terminates because of a syntax error. |
| Owner (documented) | Member 4 |

### FR-05 - External command execution with PATH search

| Field | Content |
|---|---|
| Requirement ID | FR-05 |
| Feature | External Command Execution |
| Priority | High |
| Description | For a command that is not a built-in the shell shall create a child process with fork() and replace it with the program using execvp(), searching the directories in PATH when the name contains no slash. |
| Expected system behaviour | Arguments are passed unchanged (after quote removal and expansion) as argv. A name containing / is used as a path and is not searched in PATH. |
| Error / exception behaviour | See FR-07 for exec failures. If fork() or pipe() fails, already-started children are reaped, an error is printed and the status is 1. |
| Owner (documented) | Member 1 |

### FR-06 - Foreground wait and exit status

| Field | Content |
|---|---|
| Requirement ID | FR-06 |
| Feature | External Command Execution |
| Priority | High |
| Description | The shell shall wait for every foreground child before reading the next command and shall record the exit status of the last command of a pipeline in $?. |
| Expected system behaviour | Normal exit -> exit code. Death by signal N -> 128+N and a message (strsignal) on stderr, except SIGINT (newline only) and SIGPIPE (silent). |
| Error / exception behaviour | waitpid() interrupted by a signal is retried. |
| Owner (documented) | Member 1 |

### FR-07 - Invalid command handling

| Field | Content |
|---|---|
| Requirement ID | FR-07 |
| Feature | External Command Execution |
| Priority | High |
| Description | When a command cannot be executed the shell shall print a diagnostic, set the status and continue. |
| Expected system behaviour | Name not found in PATH -> 'mysh: <name>: command not found', status 127. Path with / not found -> 'No such file or directory', status 127. Found but not executable (e.g. EACCES) -> strerror message, status 126. |
| Error / exception behaviour | The child exits; the shell prompts again. |
| Owner (documented) | Member 4 |

### FR-08 - Built-in cd

| Field | Content |
|---|---|
| Requirement ID | FR-08 |
| Feature | Built-in Commands |
| Priority | High |
| Description | cd [dir] shall change the working directory of the shell process itself; cd with no argument shall use $HOME; cd - shall return to $OLDPWD and print the new directory. PWD and OLDPWD shall be updated. |
| Expected system behaviour | Runs in the shell process (not a child) so the change persists. |
| Error / exception behaviour | Missing/inaccessible directory -> 'cd: <dir>: <strerror>', status 1. More than one argument -> 'too many arguments', status 1. HOME or OLDPWD unset when needed -> error, status 1. |
| Owner (documented) | Member 2 |

### FR-09 - Built-in pwd

| Field | Content |
|---|---|
| Requirement ID | FR-09 |
| Feature | Built-in Commands |
| Priority | High |
| Description | pwd shall print the absolute path of the current working directory followed by a newline. |
| Expected system behaviour | Output can be redirected or piped like any command. |
| Error / exception behaviour | If getcwd() fails, 'pwd: <strerror>' and status 1. |
| Owner (documented) | Member 2 |

### FR-10 - Built-in exit

| Field | Content |
|---|---|
| Requirement ID | FR-10 |
| Feature | Built-in Commands |
| Priority | High |
| Description | exit [n] shall terminate the shell with status n (0-255, taken modulo 256), or with the status of the last command when n is omitted. Remaining input is not executed. |
| Expected system behaviour | Background jobs are not signalled; they are left running. |
| Error / exception behaviour | Non-numeric argument -> 'exit: <arg>: numeric argument required' and the shell exits with status 2. More than one argument -> error, shell does not exit, status 1. |
| Owner (documented) | Member 4 |

### FR-11 - Built-in help

| Field | Content |
|---|---|
| Requirement ID | FR-11 |
| Feature | Built-in Commands |
| Priority | Medium |
| Description | help shall print the list of built-in commands with usage and a summary of the supported operators and variable forms. |
| Expected system behaviour | Output goes to stdout and can be redirected. |
| Error / exception behaviour | None (always status 0). |
| Owner (documented) | Member 4 |

### FR-12 - Environment variables

| Field | Content |
|---|---|
| Requirement ID | FR-12 |
| Feature | Environment and Expansion |
| Priority | High |
| Description | The shell shall let the user set, remove and list environment variables: export NAME=VALUE, export NAME, unset NAME..., env, and a bare NAME=VALUE command. Variables are visible to child processes. |
| Expected system behaviour | Shell variables and environment variables are the same set (every variable is exported). A line consisting only of assignments sets them in the shell process. |
| Error / exception behaviour | An invalid identifier -> "<cmd>: '<arg>': not a valid identifier", status 1. |
| Owner (documented) | Member 2 |

### FR-13 - Variable and tilde expansion

| Field | Content |
|---|---|
| Requirement ID | FR-13 |
| Feature | Environment and Expansion |
| Priority | High |
| Description | Outside single quotes the parser shall expand $NAME, ${NAME}, $? (last status), $$ (shell PID), and a leading ~ (or ~/...) to $HOME. Expansion of one pipeline happens after the previous pipeline finished. |
| Expected system behaviour | An unset variable expands to nothing; an unquoted expansion that yields an empty string is dropped, a quoted one is kept as an empty argument. A lone $ is literal. |
| Error / exception behaviour | Malformed ${...} -> 'bad substitution' syntax error (FR-04). ~user is not supported and stays literal. |
| Owner (documented) | Member 2 |

### FR-14 - Output redirection >

| Field | Content |
|---|---|
| Requirement ID | FR-14 |
| Feature | I/O Redirection |
| Priority | High |
| Description | cmd > file shall send the standard output of cmd to file, creating it (mode 0644 before umask) or truncating it. |
| Expected system behaviour | Works for external commands and built-ins. If > is given more than once the last target is used. |
| Error / exception behaviour | See FR-17. |
| Owner (documented) | Member 3 |

### FR-15 - Append redirection >>

| Field | Content |
|---|---|
| Requirement ID | FR-15 |
| Feature | I/O Redirection |
| Priority | High |
| Description | cmd >> file shall append the standard output of cmd to file, creating it if it does not exist. |
| Expected system behaviour | Existing content is preserved. |
| Error / exception behaviour | See FR-17. |
| Owner (documented) | Member 3 |

### FR-16 - Input redirection <

| Field | Content |
|---|---|
| Requirement ID | FR-16 |
| Feature | I/O Redirection |
| Priority | High |
| Description | cmd < file shall connect the standard input of cmd to file. |
| Expected system behaviour | Works for external commands and built-ins; in a pipeline an explicit < on the first command replaces the inherited input. |
| Error / exception behaviour | See FR-17. |
| Owner (documented) | Member 3 |

### FR-17 - Redirection error handling

| Field | Content |
|---|---|
| Requirement ID | FR-17 |
| Feature | I/O Redirection |
| Priority | High |
| Description | If a redirection target cannot be opened the command shall not run, the shell shall print '<file>: <strerror>' and the status shall be 1. |
| Expected system behaviour | For built-ins run in the shell process the standard descriptors are restored, so the shell itself is unaffected. |
| Error / exception behaviour | Example: cat < missing.txt; echo hi > nodir/x. |
| Owner (documented) | Member 4 |

### FR-18 - Pipelines

| Field | Content |
|---|---|
| Requirement ID | FR-18 |
| Feature | Pipelines and Sequencing |
| Priority | High |
| Description | cmd1 \| cmd2 \| ... shall run all commands concurrently, connecting standard output of each to standard input of the next with pipe(). The pipeline status is that of the last command. There is no fixed limit on the number of stages. |
| Expected system behaviour | Built-ins used inside a pipeline run in a child process. Parent closes all unused pipe ends so readers see end-of-file. |
| Error / exception behaviour | A stage that fails to exec does not block the others (its pipe end closes). A syntax error is reported per FR-04. |
| Owner (documented) | Member 3 |

### FR-19 - Command sequencing with ;

| Field | Content |
|---|---|
| Requirement ID | FR-19 |
| Feature | Pipelines and Sequencing |
| Priority | Medium |
| Description | Pipelines separated by ; (or a newline) shall be executed one after another regardless of the earlier status. |
| Expected system behaviour | Each pipeline is parsed just before it runs, so 'export X=1; echo $X' prints 1. |
| Error / exception behaviour | A syntax error stops processing of the rest of that line (FR-04). |
| Owner (documented) | Member 1 |

### FR-20 - Background execution with &

| Field | Content |
|---|---|
| Requirement ID | FR-20 |
| Feature | Background Execution |
| Priority | High |
| Description | A pipeline terminated by & shall be started and the shell shall immediately continue without waiting. Interactively the shell prints [id] pid on start and [id]+ Done <command> when it has finished (reported before the next prompt). |
| Expected system behaviour | Background processes read from /dev/null unless redirected, ignore SIGINT, and are reaped with waitpid(WNOHANG) so they do not remain zombies. Status of the & pipeline is 0. |
| Error / exception behaviour | If the job table (64 entries) is full the job still runs but is not reported. |
| Owner (documented) | Member 3 |

### FR-21 - Signal handling

| Field | Content |
|---|---|
| Requirement ID | FR-21 |
| Feature | Signal Handling |
| Priority | High |
| Description | In interactive mode Ctrl+C shall interrupt the current input line or foreground job without terminating the shell; Ctrl+\ and Ctrl+Z shall not stop or kill the shell or its foreground jobs (no job control). |
| Expected system behaviour | At the prompt Ctrl+C abandons the line, prints a newline, sets $? to 130 and redraws the prompt. A foreground child receives the default SIGINT action; the shell reports status 130. Background jobs are not affected by Ctrl+C. |
| Error / exception behaviour | SIGPIPE keeps its default action in children. |
| Owner (documented) | Member 3 |

### FR-22 - Graceful termination

| Field | Content |
|---|---|
| Requirement ID | FR-22 |
| Feature | Command Loop and Input Sources |
| Priority | High |
| Description | The shell shall terminate cleanly (freeing its state and returning the proper exit status) on exit or on end-of-input (Ctrl+D interactively, EOF on a pipe or file). |
| Expected system behaviour | Interactively 'exit' is printed on Ctrl+D. The exit status is that of the last command (or the exit argument). |
| Error / exception behaviour | None. |
| Owner (documented) | Member 1 |

## Non-functional requirements

| ID | Category | Requirement | Verification |
|---|---|---|---|
| NFR-01 | Performance | When a pipeline is terminated by &, the shell shall return to the prompt within 500 ms of reading the line, regardless of how long the job runs. On the reference environment the shell shall run 1000 consecutive external commands (true) in at most 5 s (mean <= 5 ms each) and 1000 consecutive built-in commands in at most 1 s. | NF-01, NF-02, NF-03 |
| NFR-02 | Robustness | The shell shall process without crash, hang or memory error: a 100000-character argument, a command with 2000 arguments, a 10-stage pipeline, 300 consecutive pipelines, and 200000 randomly generated command lines in the parser fuzz test (0 failures allowed). | TC-54, TC-55, TC-57, TC-77, SC-12, SC-13 |
| NFR-03 | Usability | 100% of diagnostics shall be written to stderr as 'mysh: <reason>' (usually 'mysh: <subject>: <cause>'); help shall list all 7 built-ins in at most 25 lines of at most 80 characters; the interactive prompt shall show the current working directory. | NF-04, NF-08, TC-34, ST-01 |
| NFR-04 | Maintainability | All source files shall compile with 0 warnings under gcc -std=c11 -Wall -Wextra -Wpedantic -Werror; each of the 6 modules shall publish its interface in a header file; adding a built-in shall require only one new entry in the built-in table and one new function. | NF-05 (compiler); inspection of builtins.c table |
| NFR-05 | Portability | The sources shall compile with 0 warnings both as C11 and as C99 with POSIX.1-2008 feature macros, using only the C library and POSIX interfaces, and all automated tests shall pass on Ubuntu 24.04 with gcc 13.3. Other operating systems are not yet verified. | NF-06, whole suite on Ubuntu 24.04 |
| NFR-06 | Security | The security requirements SR-01 to SR-10 of section 6.3 shall all be satisfied. | SC-01 to SC-13, ST-03, ST-04, ST-08, ST-12 |
| NFR-07 | Testability | Every functional requirement shall have at least one automated test that runs without a terminal (-c, script file or stdin), and the whole suite shall be runnable with a single command (make test) that returns a non-zero status on any failure. | RTM (Appendix C); make test |
| NFR-08 | Memory safety and resource management | The unit and functional suites and the fuzz run shall produce 0 reports under AddressSanitizer, UndefinedBehaviorSanitizer and LeakSanitizer, and after 300 consecutive pipelines an executed program shall see no open descriptor other than 0, 1 and 2. | ST-12, SC-09, TC-77 |
| NFR-09 | Reliability | After each of 10 different kinds of user error (unknown command, bad cd, missing redirection file, syntax error, bad export, non-executable file, unsupported operator, ...) the next input line shall execute normally; 0 of the 10 shall terminate the shell. | NF-07, TC-05, TC-08, TC-16, TC-41, ST-03 |
