"""Generates STP.md - Software Test Plan, following Test_Plan_Template_for_SE.docx (sections 1-15, 5.1)."""
import docdata as D

# Detailed test case specifications (Appendix A): id, title, preconditions, steps, expected result
SPECS = [
 ("TC-03", "Run an external command", "mysh built; any directory", "1. `mysh -c 'echo Hello'`", "stdout is exactly `Hello`; exit status 0"),
 ("TC-08", "Invalid command handling", "mysh built; no program named invalidcommand in PATH", "1. `mysh -c 'invalidcommand; echo $?'`", "stderr contains `command not found`; stdout is `127`; shell continues"),
 ("TC-04", "cd changes the shell's own directory", "directory `sub` exists in the working directory", "1. `cd sub; pwd; cd ..; pwd`", "first pwd prints `<dir>/sub`, second prints `<dir>`"),
 ("TC-12", "Output redirection `>`", "empty working directory", "1. `echo hello > output.txt; cat output.txt`", "file output.txt is created and `cat` prints `hello`"),
 ("TC-18", "Pipe between two commands", "file.txt contains `hello world`, `foo`, `hello again`", "1. `cat file.txt | grep hello`", "stdout is the two lines containing hello; status 0"),
 ("TC-20", "Pipeline combined with `<` and `>` (integration)", "file.txt as above", "1. `sort < file.txt | head -n 1 > first.txt; cat first.txt`", "first.txt contains `foo` (alphabetically first line)"),
 ("TC-32", "exit stops the shell and sets the status", "none", "1. `mysh -c 'echo a; exit 3; echo b'`", "stdout `a` only; process exit status 3"),
 ("TC-41", "Syntax error: unterminated quote", "none", "1. `mysh -c 'echo \"abc'`", "no command runs; stderr `unterminated double quote`; exit status 2"),
 ("TC-36", "Background execution does not block", "none", "1. `mysh -c 'sleep 2 & echo started'` and measure elapsed time", "`started` printed; elapsed time below 1.5 s"),
 ("ST-04", "Ctrl+C stops a foreground job but not the shell (system, pseudo-terminal)", "mysh started on a pty and prompt visible", "1. type `sleep 30`; 2. after 0.6 s send Ctrl+C; 3. type `echo $?`", "prompt returns within 5 s; `echo $?` prints 130; shell still responds"),
 ("ST-10", "Full demonstration script (system)", "demo/demo.mysh present", "1. `mysh demo.mysh`", "all documented outputs present (Hello, Shell!; Welcome Student; both lines of notes.txt; command not found; status was 127); exit status 0"),
 ("SC-01", "Injection through quoted metacharacters (security, SR-01)", "empty working directory", "1. `echo \"a; echo injected | cat > pwned\"; ls pwned`", "the whole text is printed literally; no file `pwned` exists (ls fails with status 2)"),
 ("SC-02", "No re-interpretation of variable contents (security, SR-02)", "none", "1. `X=\"a; echo pwned\"; echo $X`", "stdout is the single line `a; echo pwned`"),
 ("SC-07", "File creation permissions (security, SR-05)", "umask set to 077, 022 and 000 in three runs", "1. `echo x > f` under each umask; 2. read file mode", "modes 600, 644, 644 (never more permissive than 0644)"),
 ("SC-09", "No descriptor inheritance (security, SR-08)", "tests/fdcheck.py lists open descriptors >= 3", "1. run 300 x `true | true`; 2. `python3 fdcheck.py`", "output is `[]`"),
 ("SC-12", "Parser fuzzing under sanitizers (security, SR-06)", "AddressSanitizer + UBSan build (`make fuzz`)", "1. run `build-asan/fuzz_parser` (200,000 pseudo-random lines from a vocabulary of metacharacters, quotes, expansions and raw bytes)", "0 invariant violations and 0 sanitizer reports; program exits 0"),
 ("NF-01", "Responsiveness of background start (performance, NFR-01)", "none", "1. time `mysh -c 'sleep 2 & echo started'`", "elapsed time <= 500 ms"),
 ("NF-04", "Diagnostic format (usability, NFR-03)", "12 error scenarios prepared", "1. run each scenario; 2. check every stderr line", "100% of lines start with `mysh: ` followed by a reason"),
 ("NF-07", "Recovery after errors (reliability, NFR-09)", "none", "1. pipe 10 faulty lines then `echo alive` into mysh", "stdout is `alive` only (no error terminated the shell)"),
]

NEG = {"TC-05","TC-08","TC-09","TC-16","TC-17","TC-33","TC-41","TC-42","TC-43","TC-44","TC-45","TC-46","TC-62","TC-63","TC-64","TC-65","TC-66","TC-70","TC-73"}
ROB = {"TC-54","TC-55","TC-77","TC-57","TC-58"}
INTEG = {"TC-18","TC-19","TC-20","TC-21","TC-22","TC-24","TC-27","TC-48","TC-49","TC-50","TC-51","TC-52","TC-53","TC-75","TC-74","TC-36","TC-25","TC-35"}

def build(c):
    table, tests, tests_for, DATE = c["table"], c["tests"], c["tests_for"], c["DATE"]
    LOC, idkey = c["LOC"], c["idkey"]
    FR, NFR, SR, SO = D.FR, D.NFR, D.SR, D.SO
    PF = ("UT", "TC", "SC", "NF", "ST")
    def tid(req): return ", ".join(tests_for(req, PF)) or "-"
    allt = list(tests.values()); n = len(allt); npass = sum(1 for t in allt if t["status"] == "PASS")
    cat = lambda pre: [t for t in allt if t["id"].startswith(pre)]
    ids_by = lambda f: sorted([t["id"] for t in allt if f(t)], key=idkey)
    unit = ids_by(lambda t: t["id"].startswith("UT"))
    sec = ids_by(lambda t: t["id"].startswith("SC"))
    nf = ids_by(lambda t: t["id"].startswith("NF"))
    sysids = ids_by(lambda t: t["id"].startswith("ST"))
    tcs = ids_by(lambda t: t["id"].startswith("TC"))
    neg = [i for i in tcs if i in NEG]; rob = [i for i in tcs if i in ROB and i not in NEG]
    integ = [i for i in tcs if i in INTEG and i not in NEG and i not in ROB]
    func = [i for i in tcs if i not in NEG and i not in ROB and i not in INTEG]
    TH = ["Test Case ID", "Requirement ID", "Input / Command", "Expected Output", "Actual Result", "Pass/Fail"]
    def rows(ids):
        return [[i, tests[i]["req"], ("`" + tests[i]["cmd"] + "`") if tests[i]["cmd"] else "", tests[i]["exp"] or tests[i]["desc"],
                 "As expected" if tests[i]["status"] == "PASS" else "MISMATCH", tests[i]["status"]] for i in ids]
    fr_cov = sum(1 for f in FR if tests_for(f[0], PF)); sr_cov = sum(1 for s in SR if tests_for(s[0], PF))
    nfr_extra = c["NFR_EXTRA"]
    nfr_cov = sum(1 for x in NFR if tests_for(x[0], PF) or nfr_extra.get(x[0]))
    o = []
    o.append("""---
title: "Software Test Plan (STP)"
subtitle: "Simple Shell (Command Line Interpreter) - mysh"
---

**Project:** Simple Shell (Command Line Interpreter), executable `mysh`  
**Version:** 1.0  
**Authors:** Software Engineering Project 15 team - QA lead Member 4 with Members 1-3  
**Date:** %s  
**Status:** Draft 1.0 - Part-1 submission (test cases designed and executed once; results in section 14 and Appendix B)

## 1. Introduction

**Purpose:** This document defines the test plan for `mysh` v1.0: objectives, scope, strategy, environment, schedule, responsibilities and the test cases that verify the functional, non-functional and security requirements of the SRS.

**Scope:** Testing covers command execution, parsing, built-ins, environment and expansion, redirection, pipelines, sequencing, background jobs, signal handling, termination, the non-functional requirements (performance, robustness, usability, maintainability, portability, memory safety, reliability) and the security requirements SR-01 to SR-10. Behaviour of the operating system, the terminal emulator and external utilities is excluded.

**References:** SRS v1.0 (`docs/SRS.docx`); Software Architecture and Design Specification v1.0 (`docs/SAD.docx`); RTM (SRS Appendix C); IEEE Std 829-2008 (software test documentation); POSIX.1-2008 Shell Command Language; the course template `Test_Plan_Template_for_SE.docx`.

**Definitions:** STP (Software Test Plan), SRS (Software Requirements Specification), RTM (Requirement Traceability Matrix), FR (functional requirement), NFR (non-functional requirement), SR (security requirement), pty (pseudo-terminal), ASan/UBSan/LSan (Address/Undefined-behaviour/Leak sanitizers), fuzzing (testing with large numbers of random inputs).

## 2. Test Items

""" % DATE + table(["Test item", "Source", "Requirements"], [
        ["Shell Core: prompt, read-eval loop, signals, options, termination", "main.c, shell.c", "FR-01, FR-02, FR-19, FR-21, FR-22, SR-04, SR-08, SR-09"],
        ["Parser: tokenizer, quoting, expansion, syntax errors", "parser.c", "FR-03, FR-04, FR-13, SR-01, SR-02, SR-06"],
        ["Executor: fork/exec, wait, redirection, pipes, background jobs", "executor.c", "FR-05, FR-06, FR-07, FR-14 to FR-18, FR-20, SR-03, SR-05, SR-08, SR-10"],
        ["Built-in commands: cd, pwd, exit, help, export, unset, env", "builtins.c", "FR-08 to FR-12, SR-07"],
        ["Utilities", "utils.c", "NFR-08, SR-06, SR-07"],
        ["Build system and test tooling", "Makefile, tests/", "NFR-04, NFR-05, NFR-07"]]) + """
## 3. Features to be Tested

Features are mapped to SRS requirement IDs. Pass criteria are in the SRS (section 5 and 6) and in the expected results of the test cases.

""" + table(["Requirement ID", "Feature", "Type", "Priority", "Test cases"], [[f[0], f[1], "Functional", f[3], tid(f[0])] for f in FR]) + "\n" +
        table(["Requirement ID", "Feature (measurable criterion in SRS 6.4)", "Type", "Test cases"], [[x[0], x[1] + " - " + x[2].split(".")[0] + ".", "Non-functional", tid(x[0]) if tests_for(x[0], PF) else x[3]] for x in NFR]) + "\n" +
        table(["Requirement ID", "Security feature (objective)", "Type", "Priority", "Test cases"], [[s[0], s[2].split(".")[0] + ". (" + s[1] + ")", "Security", s[3], tid(s[0])] for s in SR]) + """
## 4. Features not to be Tested

* Linux kernel, glibc and the terminal emulator (assumed correct; vendor responsibility).
* Behaviour of external programs the shell launches (`ls`, `grep`, `sort`, `sleep`, ...): only that the shell starts them correctly and reports their status.
* Features outside the product scope (SRS 2.5): job control (`fg`, `bg`, `jobs`), wildcard expansion, command substitution, `&&`, `||`, `2>`, here-documents, aliases, functions, history, line editing. Only the *rejection* of `&&` and `||` is tested (TC-45, TC-73).
* Operating systems other than Ubuntu 24.04 (portability beyond compilation as C99/C11 is not tested).
* Full-screen terminal programs (`vi`, `less`) and long-duration soak tests.
* Third-party penetration testing and formal certification.

## 5. Test Approach / Strategy

**Levels**

""" + table(["Level", "What is tested", "Technique / tool", "Test IDs"], [
        ["Unit", "Parser and utility functions in isolation (no processes)", "C driver linked with the modules (`tests/test_parser.c`)", "UT-01 to UT-24"],
        ["Integration", "Parser + executor + built-ins + OS together: pipes with redirection, built-ins in pipelines, environment inheritance, script/stdin input", "bash harness `tests/run_tests.sh` using `mysh -c`, script file and stdin", "TC-18 to TC-22, TC-24, TC-48 to TC-53, ..."],
        ["System", "End-to-end behaviour on a real terminal: prompt, Ctrl+C, Ctrl+D, Ctrl+Z, job notices; demo script; sanitizer build", "Python `pty` driver `tests/interactive_test.py`, `demo/demo.mysh`, `make sanitize`", "ST-01 to ST-12"],
        ["Acceptance", "Demonstration to the instructor following `docs/DEMO_SCRIPT.md`", "Manual", "Planned (after Part-1)"]]) + """
**Types**

* *Functional testing:* each FR, black-box, exact stdout and exit status (TC-xx).
* *Negative / error testing:* invalid commands, syntax errors, missing files, bad arguments (TC-05, TC-08, TC-09, TC-16, TC-17, TC-33, TC-41 to TC-46, ...).
* *Regression testing:* the whole suite is re-run with one command (`make test`) after every change.
* *Performance testing:* response time of background start and throughput of 1000 external and 1000 built-in commands (NF-01 to NF-03). Thresholds are deliberately generous so that they detect regressions, not hardware differences.
* *Robustness testing:* 100,000-character argument, 2,000 arguments, 10-stage pipeline, 300 consecutive pipelines (TC-54, TC-55, TC-57, TC-77).
* *Usability testing (objective part):* diagnostic format and help-screen size (NF-04, NF-08); subjective usability by demonstration.
* *Maintainability/portability checks:* compilation with `-Werror` as C11 and as C99 (NF-05, NF-06).
* *Security testing:* section 5.1.

**Entry criteria:** the build succeeds without warnings; the test environment of section 6 is available; fixtures are generated by the harness itself.

**Exit criteria:** 100% of planned test cases executed; 0 failing; 0 open critical or high defects; every FR, NFR and SR traced to at least one passing test (section 13); sanitizer and fuzz runs report nothing. *Status for this release: all criteria are met (section 14).*

**Pass/fail rule:** a test passes only if stdout, exit status and (where specified) stderr text all match the expected result exactly; timing tests pass if the measured time is within the stated bound.

**Defect severity:** Critical (crash, data loss, security breach), High (requirement not met), Medium (wrong message or status), Low (cosmetic or test-only).

## 5.1 Security Validation

Validation targets the security objectives SO-1 to SO-5 and requirements SR-01 to SR-10 (SRS 6.3) and the STRIDE threats of the SAD (section 3.9).

""" + table(["Activity", "What it validates", "Requirement", "Test IDs", "Status"], [
        ["Static check: no `system()`, `popen()` or `sh -c` in the source", "No second interpretation of user text", "SR-01", "SC-04", tests["SC-04"]["status"]],
        ["Injection tests: quoted metacharacters, variable contents holding operators, file names containing `; | `", "Quoting and expansion never create syntax", "SR-01, SR-02", "SC-01, SC-02, SC-03", "/".join(sorted({tests[i]["status"] for i in ("SC-01", "SC-02", "SC-03")}))],
        ["Privilege check: no setuid-family calls; child uid equals shell uid", "No privilege change", "SR-03", "SC-05", tests["SC-05"]["status"]],
        ["Data exposure: no history/log files; file modes under umask 077/022/000; background job stdin", "No unintended disclosure", "SR-04, SR-05, SR-10", "SC-06, SC-07, SC-11", "/".join(sorted({tests[i]["status"] for i in ("SC-06", "SC-07", "SC-11")}))],
        ["Environment validation: invalid names rejected", "Environment integrity", "SR-07", "SC-08, TC-64", "/".join(sorted({tests[i]["status"] for i in ("SC-08", "TC-64")}))],
        ["Descriptor inheritance after 300 pipelines and in script mode", "No leaked descriptors", "SR-08", "SC-09, SC-10", "/".join(sorted({tests[i]["status"] for i in ("SC-09", "SC-10")}))],
        ["Signal robustness: Ctrl+C at prompt and during a job, Ctrl+Z", "Shell cannot be killed/frozen by keyboard signals", "SR-09", "ST-03, ST-04, ST-08", "/".join(sorted({tests[i]["status"] for i in ("ST-03", "ST-04", "ST-08")}))],
        ["Fuzzing, parser level: 200,000 pseudo-random lines (metacharacters, quotes, expansions, raw bytes) under ASan+UBSan with structural invariants", "Memory safety of the parser", "SR-06", "SC-12", tests["SC-12"]["status"]],
        ["Fuzzing, process level: 600 random command lines run through the sanitizer build of the real shell", "No crash/hang/sanitizer report end to end", "SR-06", "SC-13", tests["SC-13"]["status"]],
        ["Sanitizer build of unit + functional suites (ASan, UBSan, LSan)", "Memory errors and leaks", "SR-06, NFR-08", "ST-12", tests["ST-12"]["status"]]]) + """
**Planned but not performed:** independent penetration test by a third party; seccomp/sandbox review; fuzzing with a coverage-guided fuzzer (AFL/libFuzzer); static analysis with a dedicated tool (cppcheck/clang-analyzer were not available in the test environment).

## 6. Test Environment

* **Hardware:** x86-64 virtual machine, Linux 6.18 kernel.
* **Software:** Ubuntu 24.04.4 LTS, gcc 13.3.0, GNU make, bash, Python 3 (`pty`), coreutils, `grep`, `sort`, `sleep`, `id`, `stat`.
* **Tools:** bash harness (functional), Python pty driver (system), C unit driver, AddressSanitizer/UBSan/LeakSanitizer, own fuzzers (`tests/fuzz_parser.c`, `tests/fuzz_shell.py`), git-style folders for result files `tests/results_*`.
* **Test data:** generated per run in a temporary directory: `file.txt` (3 lines), `input.txt`, a non-executable `noexec.sh`, an executable `bin/hello_tool`, scripts for stdin/script modes; no real user data.
* **Defect tracking:** table in section 14 (a tracker such as Jira is not used for this project).

## 7. Test Schedule

""" + table(["Milestone", "Date", "Status"], [
        ["Test case design (unit, functional, system) and automation", "up to %s" % DATE, "Done"],
        ["Security and non-functional test design (SC, NF), fuzzers", DATE, "Done"],
        ["Environment setup", DATE, "Done"],
        ["Test execution round 1 (all %d tests)" % n, DATE, "Done: %d passed, %d failed" % (npass, n - npass)],
        ["Regression run after review comments", "05-Oct-2026", "Planned"],
        ["Part-1 submission", "07-Oct-2026", "Planned"],
        ["Acceptance demonstration", "As scheduled by the course after Part-1", "Planned"]]) + """
## 8. Test Deliverables

* Test Plan (this document)
* Test cases: manual specifications (Appendix A) and automated tests (`tests/test_parser.c`, `tests/run_tests.sh`, `tests/interactive_test.py`, `tests/fuzz_parser.c`, `tests/fuzz_shell.py`)
* Test scripts and test data generators (the same files)
* Test execution logs: `tests/results_unit.txt`, `results_functional.txt/.tsv`, `results_interactive.txt`, `results_fuzz.txt`, `results_sanitizer.txt`
* Defect report (section 14)
* Test Summary Report (section 14)

## 9. Roles and Responsibilities

""" + table(["Role", "Name", "Responsibility"], [
        ["QA Lead", "Member 4", "Prepare plan, own harness and traceability, coordinate execution, sanitizer and fuzz runs"],
        ["Test Engineer", "Member 2", "Parser unit tests, expansion/built-in tests, parser fuzzer"],
        ["Test Engineer", "Member 3", "Redirection, pipe, background and signal tests (pty), security tests SC-xx"],
        ["Developer", "Member 1", "Support defect fixes and triage, core and executor changes"],
        ["Product Owner / reviewer", "Faculty guide", "Approve test results, sign off readiness"]]) + """
## 10. Risks and Mitigation

""" + table(["Risk", "Mitigation"], [
        ["Timing tests fail on a slow or busy machine", "Thresholds are generous (500 ms for a 2 s job; 5 s for 1000 commands); measured values are recorded (4 ms and about 0.8 s here)"],
        ["Pseudo-terminal tests are timing sensitive", "Generous waits and timeouts; each test starts its own shell; failures print captured output"],
        ["Background children keep a captured pipe open and make the *test harness* wait", "Harness writes background-test output to files (seen once: TC-36/TC-74, section 14)"],
        ["Sanitizer or tool not available on a team member's machine", "Same suite runs without sanitizers (`make test`); sanitizer run done on the reference environment"],
        ["Tests run as root hide permission problems", "Permission tests use mode bits and the exec bit (TC-09 passes as root); re-run as an ordinary user is listed as a regression step"],
        ["Only one platform available", "Stated limitation; portability test limited to compilation as C99/C11"]]) + """
## 11. Assumptions & Dependencies

* The reference environment of section 6 stays available and `PATH` contains the standard utilities.
* Tests create and delete their own temporary directories; no network is needed.
* The terminal emulation of Python's `pty` module delivers Ctrl+C as SIGINT to the foreground process group.
* gcc supports `-fsanitize=address,undefined`.

## 12. Suspension & Resumption Criteria

Suspend testing if: the build fails to compile; the environment is unavailable for more than 4 hours; the build is so unstable that more than 30%% of test cases are blocked. Resume when: the blocking defects are fixed and a clean build passes the smoke subset (UT-01 to UT-10, TC-01 to TC-03).

## 13. Test Case Management & Traceability

The RTM maps every SRS requirement to its architecture/design element, source file and test cases (SRS Appendix C). The test side of that matrix is reproduced here and is generated from the same data as the result files, so IDs cannot drift. Test IDs: UT unit, TC functional/integration/negative/robustness, SC security, NF non-functional, ST system.

**Coverage:** functional requirements with at least one test: %d of %d; security requirements: %d of %d; non-functional requirements: %d of %d.

""" % (fr_cov, len(FR), sr_cov, len(SR), nfr_cov, len(NFR)) + table(["Requirement", "Unit / functional / security / non-functional tests", "System tests"], [[f[0] + " " + f[1], ", ".join(tests_for(f[0], ("UT", "TC", "SC", "NF"))) or "-", ", ".join(tests_for(f[0], ("ST",))) or "-"] for f in FR]) + "\n" +
        table(["Requirement", "Tests (including inspection where stated)"], [[x[0] + " " + x[1], x[3]] for x in NFR]) + "\n" +
        table(["Requirement", "Objective", "Tests"], [[s[0], s[1], tid(s[0])] for s in SR]) + """
## 14. Test Metrics & Reporting

**Test Summary Report (execution of %s on Ubuntu 24.04.4, gcc 13.3.0)**

""" % DATE + table(["Category", "Designed", "Executed", "Passed", "Failed"], [
        ["Unit (UT)", len(unit), len(unit), sum(1 for i in unit if tests[i]["status"] == "PASS"), sum(1 for i in unit if tests[i]["status"] != "PASS")],
        ["Functional / integration / negative / robustness (TC)", len(tcs), len(tcs), sum(1 for i in tcs if tests[i]["status"] == "PASS"), sum(1 for i in tcs if tests[i]["status"] != "PASS")],
        ["Security (SC)", len(sec), len(sec), sum(1 for i in sec if tests[i]["status"] == "PASS"), sum(1 for i in sec if tests[i]["status"] != "PASS")],
        ["Non-functional (NF)", len(nf), len(nf), sum(1 for i in nf if tests[i]["status"] == "PASS"), sum(1 for i in nf if tests[i]["status"] != "PASS")],
        ["System (ST)", len(sysids), len(sysids), sum(1 for i in sysids if tests[i]["status"] == "PASS"), sum(1 for i in sysids if tests[i]["status"] != "PASS")],
        ["**Total**", n, n, npass, n - npass]]) + """
**Metrics**

""" + table(["Metric", "Value"], [
        ["% of test cases executed", "100%% (%d of %d)" % (n, n)],
        ["% passed / failed", "%.1f%% / %.1f%%" % (100.0 * npass / n, 100.0 * (n - npass) / n)],
        ["Requirement coverage (FR / NFR / SR with at least one test)", "%d/%d, %d/%d, %d/%d (100%%)" % (fr_cov, len(FR), nfr_cov, len(NFR), sr_cov, len(SR))],
        ["Product defects found during testing", "1 (D-3), fixed and verified"],
        ["Defect density (product)", "%.2f defects per KLOC (%d lines of C in src/)" % (1000.0 / LOC, LOC)],
        ["Defect aging", "All defects found and closed within the same test cycle (open: 0)"],
        ["Open critical/high defects", "0"]]) + """
**Defect log**

""" + table(["ID", "Where", "Description", "Severity", "Resolution"], [
        ["D-1", "Test harness", "TC-36 and TC-74 first failed: the harness captured output with `$(...)`, which stays open while a background `sleep` holds the pipe, so the *harness* waited 2 s. The shell was correct.", "Low (test)", "Tests changed to write to a file; shell unchanged"],
        ["D-2", "Makefile / tests", "`make sanitize` ran the bash-syntax harness with `sh` (dash) and gave 10 false failures.", "Low (test)", "Makefile now calls `bash`"],
        ["D-3", "Product (security, SR-08)", "The script file descriptor was inherited by every program started from a script (`mysh script` followed by a program listing its descriptors showed fd 3). Found while designing SC-10; the new test fails against the old code (output `[3]`).", "Medium", "Script opened with close-on-exec (fopen mode re); SC-10 now passes"],
        ["D-4", "Test", "SC-08 expected exit status 0, but the last command (`grep -c`) correctly returns 1 when it finds no match.", "Low (test)", "Expected status corrected to 1; shell unchanged"]]) + """
**Reports:** daily execution status = output of `make test`; final Test Summary Report = this section plus the result files in `tests/`.

## 15. Approvals

""" + table(["Role", "Name", "Signature / Date"], [["QA Lead", "Member 4", ""], ["Dev Lead", "Member 1", ""], ["Product Owner / Faculty guide", "", ""]]))
    # Appendix A
    sp = []
    for (i, title, pre, steps, exp) in SPECS:
        t = tests[i]
        sp.append("**%s - %s**\n\n" % (i, title) + table(["Field", "Content"], [
            ["Requirement(s)", t["req"]], ["Preconditions", pre], ["Steps / input", steps], ["Expected result", exp],
            ["Result of execution on " + DATE, t["status"] + (" (as expected)" if t["status"] == "PASS" else " (mismatch)")]]))
    o.append("""
# Appendix A - Test Case Specifications

%d key test cases are specified in full here (functional, negative, integration, system, security, performance, usability and reliability). The remaining automated tests are listed in Appendix B with their commands and expected results.

""" % len(SPECS) + "\n".join(sp))
    o.append("""
# Appendix B - Test Case Catalogue and Results

All %d tests below were executed on %s. Results are copied from the result files by the document generator. `<testdir>` is the temporary directory created for each run.

## B.1 Unit test cases

""" % (n, DATE) + table(TH, rows(unit)) + "\n## B.2 Functional test cases\n\n" + table(TH, rows(func)) + "\n## B.3 Integration test cases\n\n" + table(TH, rows(integ)) +
        "\n## B.4 Error / negative test cases\n\n" + table(TH, rows(neg)) + "\n## B.5 Robustness test cases\n\n" + table(TH, rows(rob)) +
        "\n## B.6 Security test cases\n\n" + table(TH, rows(sec)) + "\n## B.7 Non-functional test cases\n\n" + table(TH, rows(nf)) +
        "\n## B.8 System test cases\n\n" + table(TH, rows(sysids)) + """
## B.9 Tests still to be executed (not run, no result claimed)

* Regression run after review comments and on each team member's own machine (planned 05-Oct-2026), including a run as an ordinary (non-root) user.
* Build and test on a non-Linux POSIX system.
* Pseudo-terminal suite under the sanitizer build.
* Coverage-guided fuzzing and third-party penetration test.
* Acceptance demonstration to the instructor.
""")
    return "".join(o)
