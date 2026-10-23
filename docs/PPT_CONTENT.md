# Presentation Content (15 slides)

## Slide 1: Title

* Simple Shell (Command Line Interpreter)
* Software Engineering Project 15
* Team: Member 1, Member 2, Member 3, Member 4

**Suggested diagram/screenshot:** Title slide with project name and team

**Speaker explanation:** Introduce the project: a Unix-like shell written in C, built as a software-engineering project with requirements, design, tests and traceability.

## Slide 2: Problem Statement

* "A simple Unix-like shell to execute commands from the command line."
* Language: C, Linux/POSIX
* Deliverables: working shell, SRS, design, tests, RTM

**Suggested diagram/screenshot:** Screenshot of the prompt

**Speaker explanation:** State the problem in one sentence and what we deliver beyond code.

## Slide 3: Motivation

* The shell is every user's interface to the OS
* Building one teaches fork/exec/wait, pipes, redirection, signals
* Practice of requirements-first engineering

**Suggested diagram/screenshot:** Icon: terminal window

**Speaker explanation:** Explain why a shell is a good project: small enough to finish, rich enough to touch core OS concepts.

## Slide 4: Objectives

* Run commands and built-ins
* Redirection, pipes, background jobs
* Stable error and signal handling
* SRS + design + tests + traceability

**Suggested diagram/screenshot:** Checklist graphic

**Speaker explanation:** Objectives map directly to requirement groups in the SRS.

## Slide 5: Proposed Solution

* Modular C program in 6 source modules
* Parser -> Pipeline structure -> Executor
* One pipeline parsed and executed at a time
* POSIX system calls only, no libraries

**Suggested diagram/screenshot:** docs/diagrams/01_architecture.png

**Speaker explanation:** Walk through the architecture figure from user to kernel.

## Slide 6: Functional Features

* 22 functional requirements, 9 features
* cd pwd exit help export unset env
* < > >> | ; &  quotes, $VAR, ~
* Ctrl+C / Ctrl+D handling, exit codes 126/127/128+N

**Suggested diagram/screenshot:** Table of features from SRS section 5

**Speaker explanation:** Summarise features; emphasise that each has an ID and a test.

## Slide 7: Architecture

* Shell Core: loop, prompt, signals
* Parser: text -> Command/Pipeline
* Executor: fork, exec, pipes, redirs, jobs
* Built-ins and Utilities

**Suggested diagram/screenshot:** docs/diagrams/02_components.png

**Speaker explanation:** Show module dependencies; point out that they mirror the source files.

## Slide 8: Command Execution Flow

* Lone built-in / assignment runs in the shell
* Otherwise fork one child per command
* Child: dup2 pipes, redirections, execvp
* Parent: wait, or register background job

**Suggested diagram/screenshot:** docs/diagrams/04_execution_flow.png

**Speaker explanation:** Explain the decision at the top: why cd must not run in a child.

## Slide 9: Implementation

* parse_next_pipeline(), read_word()
* execute_pipeline(), exec_child(), apply_redirections()
* SIGINT handler sets a flag; no SA_RESTART
* Zero warnings with -Wall -Wextra -Wpedantic

**Suggested diagram/screenshot:** Code snippet of the fork loop

**Speaker explanation:** Highlight two or three design decisions from DESIGN.md section 9.

## Slide 10: Team Contribution

* Member 1: Shell core and process execution (FR-01, FR-02, FR-05, FR-06, FR-19, FR-22)
* Member 2: Parser, expansion, built-ins and environment (FR-03, FR-08, FR-09, FR-12, FR-13)
* Member 3: Redirection, pipes, background jobs and signals (FR-14, FR-15, FR-16, FR-18, FR-20, FR-21)
* Member 4: Error handling, exit/help built-ins, integration and verification (FR-04, FR-07, FR-10, FR-11, FR-17)

**Suggested diagram/screenshot:** Product-ownership table

**Speaker explanation:** Each member owns functional requirements in named modules; testing and documentation are additional.

## Slide 11: Testing

* 24 unit + 74 functional + 10 terminal + sanitizer run
* Every FR traced to an executed test (RTM)
* Automated: make test, make sanitize
* Still to do: non-Linux, manual full-screen programs

**Suggested diagram/screenshot:** Screenshot of make test summary

**Speaker explanation:** Be explicit about what was and was not executed.

## Slide 12: Demonstration

* Basic commands and cd/pwd
* Variables, > >> <
* Pipes
* Background job and Ctrl+C
* Errors and exit

**Suggested diagram/screenshot:** Live terminal

**Speaker explanation:** Follow docs/DEMO_SCRIPT.md step by step.

## Slide 13: Results

* 130 of 130 designed tests pass on Ubuntu 24.04
* No sanitizer findings (unit + functional)
* Two early test failures were harness bugs, fixed

**Suggested diagram/screenshot:** Bar or table of test results

**Speaker explanation:** Report results honestly, including the harness issue we found.

## Slide 14: Limitations / Future Work

* No job control, globbing, &&, ||, 2>
* No history / line editing
* Tested on Linux only
* Next: job control, globbing, stderr redirection

**Suggested diagram/screenshot:** Roadmap graphic

**Speaker explanation:** State limitations openly; they are documented in the SRS section 2.5.

## Slide 15: Conclusion

* A working, documented, tested shell
* Requirements -> design -> code -> tests are traceable
* Thank you - questions?

**Suggested diagram/screenshot:** Team photo or logo

**Speaker explanation:** Close by restating the engineering outcome, then take questions.

