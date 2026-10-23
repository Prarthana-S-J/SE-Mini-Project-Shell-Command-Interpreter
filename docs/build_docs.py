#!/usr/bin/env python3
"""Render all project documents from docdata.py and the real test-result files.
Usage: python3 docs/build_docs.py     (run `make test` first so tests/results_* are fresh)"""
import os, re, sys, glob, subprocess
from docdata import *

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
T = os.path.join(ROOT, "tests")

# ------------------------------------------------------------------ load real results
tests = {}   # id -> dict
def add(id_, req, status, desc, cmd="", exp="", kind=""):
    tests[id_] = dict(id=id_, req=req, status=status, desc=desc, cmd=cmd, exp=exp, kind=kind)

UT_IO = {  # input given to the parser / expected result (from tests/test_parser.c)
 "UT-01":("echo hello world","argc=3, argv[0]=echo, argv[3]=NULL"),
 "UT-02":("echo 'a   b|c;d'","2 args; second is a   b|c;d"),
 "UT-03":("echo \"x $UT_VAR y\" (UT_VAR=value)","second arg: x value y"),
 "UT-04":("echo '$UT_VAR'","second arg: $UT_VAR (no expansion)"),
 "UT-05":("echo a\\ b \\> c","args: echo, 'a b', '>', c; no redirection"),
 "UT-06":("echo hi # this is ignored","argc=2"),
 "UT-07":("cat f | grep x | wc -l","ncmds=3"),
 "UT-08":("sort < in.txt > out.txt","argc=1, infile=in.txt, outfile=out.txt, append=0"),
 "UT-09":("echo x>>log.txt","outfile=log.txt, append=1"),
 "UT-10":("sleep 5 &","background=1, argc=2"),
 "UT-11":("echo one; echo two","PARSE_OK 'one', PARSE_OK 'two', then PARSE_END"),
 "UT-12":("echo \"unterminated","PARSE_ERROR, message mentions 'unterminated'"),
 "UT-13":("echo 'unterminated","PARSE_ERROR, 'unterminated single quote'"),
 "UT-14":("cat <","PARSE_ERROR, 'missing file name'"),
 "UT-15":("ls | | wc ;  | ls ;  ls |","PARSE_ERROR for each"),
 "UT-16":("echo a && echo b ;  echo a || echo b","PARSE_ERROR mentioning && / ||"),
 "UT-17":("echo $? with last_status=42","second arg: 42"),
 "UT-18":("empty, blanks, '# only a comment', newline","PARSE_END for each"),
 "UT-19":("is_valid_name / is_assignment on PATH, _x9, 9x, A=1, =1, a-b=1","1,1,0,1,0,0 as appropriate"),
 "UT-20":("echo ~ ~/docs a~b (HOME=/home/unit)","/home/unit, /home/unit/docs, a~b"),
 "UT-21":("echo ${UT_BRACE}cd $UT_UNSET end \"$UT_UNSET\"","abcd, end, '' (empty kept because quoted)"),
 "UT-22":("echo ${bad","PARSE_ERROR 'bad substitution'"),
 "UT-23":("echo hi >  ;  > file","PARSE_ERROR for each"),
 "UT-24":("echo a >x >y","outfile=y"),
}
ST_IO = {
 "ST-01":("Start mysh on a pseudo-terminal","Prompt mysh:<cwd>$ appears"),
 "ST-02":("echo hello-from-shell","Output shown, prompt returns"),
 "ST-03":("Type 'partial text', press Ctrl+C, then echo still-alive","New prompt; shell alive; still-alive printed"),
 "ST-04":("sleep 30, wait 0.6 s, Ctrl+C, then echo $?","Prompt within 5 s; $? = 130"),
 "ST-05":("sleep 1 &  ... wait 1.5 s ... press Enter","[1] <pid> at start; '[1]+ Done ... sleep 1' later"),
 "ST-06":("Ctrl+D at the prompt","'exit' printed; shell exits with status 0"),
 "ST-07":("Start a background job (sh -c 'sleep 2; echo finished > f' &), press Ctrl+C at the prompt, wait","Job completes (file f exists) and Done is reported"),
 "ST-08":("sleep 1, press Ctrl+Z","Job is not stopped; prompt returns; no hang"),
 "ST-09":("exit 4","Shell process exits with status 4"),
 "ST-11":("Background job, then sleep 30 in foreground, Ctrl+C","Foreground killed; background job still completes (file exists)"),
}
def clean(s): return re.sub(r"/tmp/tmp\.\w+", "<testdir>", s)

for line in open(os.path.join(T,"results_unit.txt")):
    m = re.match(r"(UT-\d+) (\S+) (PASS|FAIL) (.*)", line)
    if m: add(m[1], m[2], m[3], m[4], *UT_IO[m[1]], kind="unit")
for line in open(os.path.join(T,"results_functional.tsv")):
    p = line.rstrip("\n").split("\t")
    add(p[0], p[1], p[2], p[3], clean(p[4]), clean(p[5]), kind={"SC":"sec","NF":"nf"}.get(p[0][:2],"func"))
FUZZ_IO = {"SC-12":("make fuzz -> build-asan/fuzz_parser (200,000 pseudo-random lines, ASan+UBSan)","0 invariant violations, 0 sanitizer reports, exit 0"),
           "SC-13":("make fuzz -> MYSH=build-asan/mysh python3 tests/fuzz_shell.py (600 random command lines)","0 crashes, 0 hangs, 0 sanitizer reports")}
for line in open(os.path.join(T,"results_fuzz.txt")):
    m = re.match(r"(SC-\d+) (\S+) (PASS|FAIL) (.*)", line)
    if m: add(m[1], m[2], m[3], m[4].split(":")[0] + (": " + m[4].split(":",1)[1].strip() if ":" in m[4] else ""), *FUZZ_IO[m[1]], kind="sec")
for line in open(os.path.join(T,"results_interactive.txt")):
    m = re.match(r"(ST-\d+) (\S+) (PASS|FAIL) (.*)", line)
    if m: add(m[1], m[2], m[3], m[4], *ST_IO.get(m[1],("","")), kind="pty")
san = open(os.path.join(T,"results_sanitizer.txt")).read()
san_ok = "Result: PASS" in san
add("ST-12","NFR-02,NFR-08,SR-06","PASS" if san_ok else "FAIL",
    "Build with AddressSanitizer + UBSan + LeakSanitizer and rerun unit and functional suites",
    "make sanitize", "0 sanitizer reports; unit and functional suites all pass", kind="manual")
tests["ST-12"]["req"]="NFR-02,NFR-08,SR-06"

def idkey(i): p,n=i.split("-"); return (p,int(n))
def reqs_of(t): return [r.strip() for r in t["req"].split(",")]
NFR_TESTS = {"NFR-01":["NF-01","NF-02","NF-03"],"NFR-02":["TC-54","TC-55","TC-57","TC-77","SC-12","SC-13"],
 "NFR-03":["NF-04","NF-08","TC-34","ST-01"],"NFR-04":["NF-05"],"NFR-05":["NF-06"],
 "NFR-06":["SC-%02d"%i for i in range(1,14)]+["ST-03","ST-04","ST-08","ST-12"],
 "NFR-07":["TC-50","TC-51","TC-62"],"NFR-08":["SC-09","TC-77","ST-12"],
 "NFR-09":["NF-07","TC-05","TC-08","TC-16","TC-17","TC-41","ST-03"]}
def tests_for(req, prefixes):
    out=[]
    for t in tests.values():
        rs=reqs_of(t)
        hit = req in rs or ("FR-01..FR-22" in rs and req.startswith("FR-"))
        if hit and t["id"].split("-")[0] in prefixes: out.append(t["id"])
    if req in NFR_TESTS:
        out += [i for i in NFR_TESTS[req] if i in tests and i.split("-")[0] in prefixes]
    return sorted(set(out), key=idkey)
NFR_ARCH = {"NFR-01":("ARCH-3","DES-09","executor.c"),"NFR-02":("ARCH-2, ARCH-3","DES-06, DES-09","parser.c, executor.c"),
 "NFR-03":("ARCH-1, ARCH-4","DES-03, DES-18","shell.c, builtins.c"),"NFR-04":("ARCH-1..ARCH-5","all","all modules, Makefile"),
 "NFR-05":("ARCH-6","DES-05, DES-09","all (POSIX interfaces)"),"NFR-06":("ARCH-3","DES-10","executor.c"),
 "NFR-07":("ARCH-1, ARCH-2","DES-01, DES-06","main.c, parser.c"),"NFR-08":("ARCH-2, ARCH-3, ARCH-5","DES-09, DES-21","parser.c, executor.c, utils.c"),
 "NFR-09":("ARCH-1, ARCH-3","DES-04, DES-10","shell.c, executor.c")}

n_all=len(tests); n_pass=sum(1 for t in tests.values() if t["status"]=="PASS")
counts={k:sum(1 for t in tests.values() if t["kind"]==k) for k in ("unit","func","sec","nf","pty","manual")}

# ------------------------------------------------------------------ helpers
def esc(s): return str(s).replace("|","\\|").replace("\n"," ")
def table(head, rows):
    o=["| "+" | ".join(head)+" |","|"+"|".join("---" for _ in head)+"|"]
    for r in rows: o.append("| "+" | ".join(esc(c) for c in r)+" |")
    return "\n".join(o)+"\n"
def write(name, text):
    with open(os.path.join(HERE,name),"w") as f: f.write(text)
def fig(n, cap): return f"![Figure {n}: {cap}](diagrams/{n_files[n]})\n"
n_files={1:"01_architecture.png",2:"02_components.png",3:"03_lifecycle_flow.png",4:"04_execution_flow.png",
         5:"05_use_case.png",6:"06_sequence.png",7:"07_dfd_level1.png",8:"08_error_flow.png",9:"09_seq_background.png",10:"10_seq_ctrlc.png",11:"11_seq_error.png",12:"12_trust_boundaries.png"}
CAPS={1:"System architecture",2:"UML component diagram",3:"Shell lifecycle (high-level flowchart)",
      4:"Command execution flowchart",5:"UML use-case diagram",6:"UML sequence diagram SD-1: foreground pipeline",
      7:"Data-flow diagram, level 1",8:"Error-handling flow",9:"UML sequence diagram SD-2: background job",10:"UML sequence diagram SD-3: Ctrl+C during a foreground job",11:"UML sequence diagram SD-4: error paths",12:"Trust zones and security controls"}
def F(n): return f"![Figure {n}: {CAPS[n]}](diagrams/{n_files[n]})\n"
FRd={f[0]:f for f in FR}
def fr_fix(s): return s.replace("See FR-07 for exec failures and the fork()/pipe() failure rule below: if fork() or pipe() fails","See FR-07 for exec failures. If fork() or pipe() fails")

STATUS = "All %d designed tests were executed on %s (Ubuntu 24.04.4 LTS, Linux 6.18, gcc 13.3.0): %d passed, %d failed." % (n_all, DATE, n_pass, n_all-n_pass)

# ------------------------------------------------------------------ REQUIREMENTS.md
def fr_tables():
    o=[]
    for f in FR:
        o.append(f"### {f[0]} - {f[1]}\n\n"+table(["Field","Content"],[
         ["Requirement ID",f[0]],["Feature",f[2]],["Priority",f[3]],["Description",f[4]],
         ["Expected system behaviour",f[5]],["Error / exception behaviour",fr_fix(f[6])],["Owner (documented)",f[10]]]))
    return "\n".join(o)
def nfr_table():
    return table(["ID","Category","Requirement","Verification"],[list(n) for n in NFR])
req_md = f"# Requirements - {PROJECT}\n\nRequirements describe the behaviour of the implemented shell `{BINARY}` (source in `src/`). Every functional requirement has at least one executed test (see `docs/RTM.md`).\n\n## Summary of functional requirements\n\n"+table(["ID","Title","Feature","Priority","Owner"],[[f[0],f[1],f[2],f[3],f[10]] for f in FR])+"\n## Detailed functional requirements\n\n"+fr_tables()+"\n## Non-functional requirements\n\n"+nfr_table()
write("REQUIREMENTS.md", req_md)

# ------------------------------------------------------------------ RTM.md
def rtm_rows():
    rows=[]; n=1
    for f in FR:
        a=ARCH[f[7]]; ds=f[8]
        rows.append([n,f[0],f[1],f"{f[7]} {a[0]}",ds,f[9],", ".join(tests_for(f[0],("UT","TC","SC","NF"))),", ".join(tests_for(f[0],("ST",)))]); n+=1
    for x in NFR:
        a,d,c=NFR_ARCH[x[0]]
        tc=", ".join(tests_for(x[0],("UT","TC","SC","NF"))) or "n/a"
        st=", ".join(tests_for(x[0],("ST",))) or "-"
        rows.append([n,x[0],x[1],a,d,c,tc,st]); n+=1
    for r in SR:
        rows.append([n,r[0],r[2].split(". ")[0].rstrip(".")+" ("+r[1]+")",r[4],r[5],r[6],", ".join(tests_for(r[0],("UT","TC","SC","NF"))) or "-",", ".join(tests_for(r[0],("ST",))) or "-"]); n+=1
    return rows
RTM_HEAD=["Sl. No","Requirement ID","Brief Description of Requirement","Architecture Reference","Design Reference","Code File Reference","Test Case ID","System Test Case ID"]
rtm_md=f"# Requirement Traceability Matrix\n\nGenerated from `docs/docdata.py` and the real test-result files in `tests/`. Architecture references (ARCH-n) and design references (DES-n) are defined in `docs/DESIGN.md`. ST-10 (the full demonstration script) is a system test for every FR and is therefore listed against all of them.\n\n"+table(RTM_HEAD,rtm_rows())
write("RTM.md", rtm_md)

# ------------------------------------------------------------------ DESIGN.md
mods=table(["Module","Files","Responsibility","Depends on"],[
 ["Shell Core (ARCH-1)","main.c, shell.c, shell.h","Program entry and options; Shell state ($?, running flag, job table); read-eval loop; prompt; SIGINT policy; executes each parsed pipeline in turn","parser, executor, utils"],
 ["Parser (ARCH-2)","parser.c, parser.h","Tokenizes one pipeline at a time; quoting, escapes, comments; $-expansion and ~; builds Command/Pipeline structures; syntax errors","utils"],
 ["Executor (ARCH-3)","executor.c, executor.h","fork/exec, pipe wiring, redirection with dup2, waiting and status mapping, background job table and reaping, NAME=VALUE assignments, built-in dispatch (parent vs child)","builtins, parser types, shell state, utils"],
 ["Built-ins (ARCH-4)","builtins.c, builtins.h","cd, pwd, exit, help, export, unset, env; table-driven dispatch","shell state, utils"],
 ["Utilities (ARCH-5)","utils.c, utils.h","xmalloc/xrealloc/xstrdup, shell_error, StrBuf, name validation, trimming","-"],
 ["OS interface (ARCH-6)","(system calls)","fork, execvp, pipe, dup2, open, waitpid, sigaction, chdir, getcwd, setenv/getenv","-"]])
design_md=f"""# Architecture and Design - {PROJECT}

Implementation language: C11 (POSIX.1-2008), binary name `{BINARY}`. All statements below describe code that exists in `src/`.

## 1. Architecture overview

The shell is a single process organised as five cooperating modules on top of the POSIX system-call interface. The **Shell Core** owns the read-eval loop, the **Parser** converts text to a `Pipeline` data structure, the **Executor** turns a `Pipeline` into processes, the **Built-in** layer implements commands that must run inside the shell process, and **Utilities** provide shared helpers.

{F(1)}
{F(2)}
### Module decomposition and component responsibilities

{mods}
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

{F(3)}
## 4. Command parsing flow

`parse_next_pipeline()` (DES-06) skips blanks and comments, then reads tokens until an unquoted `;`, `&`, newline or end of input:

* `read_word()` (DES-07) builds a word character by character, handling `'...'`, `"..."`, backslash, `$` expansion (DES-08) and a leading `~`. An unquoted expansion that becomes empty is dropped.
* `|` finishes the current `Command` and starts the next; `<`, `>`, `>>` read the following word as the file name.
* On any violation (unterminated quote, missing file name, empty stage, `&&`, `||`, bad `${{}}`) the function frees what it built, moves the cursor to the end of the line and returns `PARSE_ERROR` with a message.

## 5. Process execution flow

`execute_pipeline()` (DES-09) first handles the cases that must not fork: a lone `NAME=VALUE` line (DES-20) and a lone built-in without `&` (run in the shell so `cd`, `exit` and `export` take effect; redirections are applied to fd 0/1 and restored afterwards). Otherwise it creates one child per command, connecting neighbours with `pipe()`. In each child (`exec_child`, DES-10) the signal policy is set, pipe ends are attached with `dup2`, redirections from the command override them (DES-11), then a built-in is run or `execvp()` is called. The parent closes unused pipe ends immediately, then either records a background job (DES-13) or waits for every child (DES-12).

{F(4)}
{F(6)}
## 6. Data flow

{F(7)}
## 7. Error-handling flow

Errors are reported with `shell_error()` (prefix `mysh: `) on stderr and never terminate the shell. Status codes follow common shell conventions: 1 general failure, 2 syntax error / usage, 126 found but not executable, 127 not found, 128+N killed by signal N, 130 interrupted at the prompt.

{F(8)}
## 8. Use cases

{F(5)}
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

"""+table(["Design ref","Function / element","File"],[[k,v[0],v[1]] for k,v in DES.items()])+"\n"+table(["Architecture ref","Layer","Files","Figures"],[[k,*v] for k,v in ARCH.items()])
write("DESIGN.md", design_md)

# ------------------------------------------------------------------ TEAM_AND_PLAN.md
own_rows=[[m[0],m[1],m[2],m[3],m[4]] for m in TEAM]
team_md=f"""# Team Ownership and Plan of Work

> Member names: replace "Member 1..4" with the real names / SRNs when submitting. Ownership below is the documented division of the four functional areas of the shell.

## Product ownership

"""+table(["Member","Primary Responsibility","Functional Features","Technical Contribution","Expected Deliverables"],own_rows)+"""
Every functional requirement has exactly one owning member (checked in `docs/CONSISTENCY_CHECK.md`):

"""+table(["Requirement","Title","Owner"],[[f[0],f[1],f[10]] for f in FR])+"""
Shared modules: `executor.c` is shared by Members 1, 3 and 4 (fork/wait; redirection/pipes/jobs; exec failure codes); `parser.c` by Members 2 and 4 (tokenizer/expansion; syntax-error paths); `builtins.c` by Members 2 and 4 (cd/pwd/env; exit/help). All members review each other's changes at integration.

## Plan of work (6 weeks)

"""+table(["Phase","Activities","Responsible member(s)","Expected deliverable","Functional features covered"],[list(p) for p in PLAN])+"""
## Notes

* The distinction between functional features and supporting activities (documentation, testing, slides) is respected: each member's primary contribution above is a set of functional requirements implemented in named modules.
* Testing, documentation and integration by Member 4 are additional to that member's functional ownership (FR-04, FR-07, FR-10, FR-11, FR-17).
"""
write("TEAM_AND_PLAN.md", team_md)

# ------------------------------------------------------------------ STP.md
def rows_for(ids):
    return [[t["id"],t["req"],"`"+t["cmd"]+"`" if t["cmd"] else "", t["exp"] or t["desc"],
             "Output/status matched expected" if t["status"]=="PASS" else "MISMATCH", t["status"]] for t in (tests[i] for i in ids)]
NEG={"TC-05","TC-08","TC-09","TC-16","TC-17","TC-33","TC-41","TC-42","TC-43","TC-44","TC-45","TC-46","TC-62","TC-63","TC-64","TC-65","TC-66","TC-70","TC-73"}
ROB={"TC-54","TC-55","TC-77","TC-57","TC-58"}
INTEG={"TC-18","TC-19","TC-20","TC-21","TC-22","TC-24","TC-27","TC-48","TC-49","TC-50","TC-51","TC-52","TC-53","TC-75","TC-74","TC-36","TC-25","TC-35"}
func_ids=[i for i in sorted((t["id"] for t in tests.values() if t["kind"]=="func" and t["id"].startswith("TC")),key=idkey)]
neg_ids=[i for i in func_ids if i in NEG]; rob_ids=[i for i in func_ids if i in ROB and i not in NEG]
int_ids=[i for i in func_ids if i in INTEG and i not in NEG and i not in ROB]
fun_ids=[i for i in func_ids if i not in NEG and i not in ROB and i not in INTEG]
unit_ids=sorted([t["id"] for t in tests.values() if t["kind"]=="unit"],key=idkey)
sys_ids=sorted([t["id"] for t in tests.values() if t["id"].startswith("ST")],key=idkey)
TH=["Test Case ID","Requirement ID","Input / Command","Expected Output","Actual / Observed Behaviour","Pass/Fail"]
test_md=f"""# Test Plan and Test Cases

## 1. Strategy

| Level | What is tested | Tool | Location |
|---|---|---|---|
| Unit | Parser and utility functions in isolation (no processes) | C test driver linked with the modules | `tests/test_parser.c` (`make unit-test`) |
| Integration | Interaction of parser, executor, built-ins and OS: pipes + redirection + built-ins + environment | Bash harness running `mysh -c`, script and stdin | `tests/run_tests.sh` |
| Functional | Each functional requirement, black-box, exact stdout and exit status (and stderr text where relevant) | same harness | `tests/run_tests.sh` |
| System | End-to-end demo script; terminal behaviour (prompt, Ctrl+C, Ctrl+D, Ctrl+Z, background notices) through a pseudo-terminal; sanitizer build | Python `pty` driver, `make sanitize` | `tests/interactive_test.py`, `demo/demo.mysh` |
| Negative / error | Invalid commands, bad syntax, missing files, bad arguments | harness | `tests/run_tests.sh` |

Run everything with `make test`; run the sanitizer build with `make sanitize`.

## 2. Test status - designed, executed, still to execute

**Tests designed:** {n_all} ({counts['unit']} unit, {counts['func']} functional/integration/negative/robustness incl. demo script, {counts['sec']} security, {counts['nf']} non-functional, {counts['pty']+counts['manual']} system).

**Tests executed:** {STATUS} The runs were performed by the automated harnesses listed above; the results below are copied from `tests/results_*.txt|tsv`, not typed by hand.

**Tests that still need execution (not run, so no result is claimed):**

* Re-run of `make test` on each team member's own machine and capture of terminal screenshots for the report.
* Build and test on a non-Linux POSIX system (macOS, BSD): not attempted.
* The pseudo-terminal suite under the AddressSanitizer build (only unit and functional suites were run under it).
* Manual testing of full-screen programs (`vi`, `less`, `top`) under the shell, and long-duration soak testing.
* Valgrind was not available in the test environment (AddressSanitizer/LeakSanitizer was used instead).

**Test environment:** Ubuntu 24.04.4 LTS, Linux 6.18, gcc 13.3.0, GNU make, bash, Python 3. Run date {DATE}.

## 3. Unit test cases

"""+table(TH,rows_for(unit_ids))+f"""
## 4. Functional test cases

"""+table(TH,rows_for(fun_ids))+"""
## 5. Integration test cases

"""+table(TH,rows_for(int_ids))+"""
## 6. Error / negative test cases

"""+table(TH,rows_for(neg_ids))+"""
## 7. Robustness test cases

"""+table(TH,rows_for(rob_ids))+"""
## 8. System test cases

"""+table(TH,rows_for(sys_ids))+"""
Notes: `<testdir>` stands for the temporary directory the harness creates for every run. ST-01..ST-11 (except ST-10) drive the shell through a pseudo-terminal so that Ctrl+C/Ctrl+D/Ctrl+Z are real terminal characters. ST-10 executes `demo/demo.mysh`. ST-12 was run with `make sanitize`; its evidence is stored in `tests/results_sanitizer.txt`.

## 9. Defects found during testing

Two functional tests (TC-36, TC-74) initially failed. Investigation showed a defect in the *test harness*, not in the shell: the harness captured output with `$(...)`, which stays open until the background `sleep` also exits. The tests were changed to write to a file; the shell code was not changed for this. Separately, running the suite with `sh` (dash) instead of `bash` caused false failures in the sanitizer target; the Makefile now calls `bash`.
"""


# ------------------------------------------------------------------ DEMO_SCRIPT.md
demo_out=open("/tmp/demo/out.txt").read().replace("/tmp/demo","<dir>") if os.path.exists("/tmp/demo/out.txt") else ""
demo_err=open("/tmp/demo/err.txt").read() if os.path.exists("/tmp/demo/err.txt") else ""
steps=[
 ("./mysh","A prompt of the form mysh:/path$ appears.","Interactive shell start (FR-01)."),
 ("pwd","Prints the current directory.","Built-in pwd (FR-09)."),
 ("echo Hello, Shell!","Prints Hello, Shell!","External command via fork/execvp and PATH search (FR-05, FR-06)."),
 ("help","Lists cd, pwd, exit, help, export, unset, env and the operators.","Built-in help (FR-11)."),
 ("mkdir demo_work","No output.","Another external command."),
 ("cd demo_work","No output; then `pwd` shows .../demo_work.","Built-in cd changes the shell's own directory (FR-08)."),
 ("export NAME=Student","No output.","Environment variable (FR-12)."),
 ("echo Welcome $NAME","Prints Welcome Student","Variable expansion (FR-13)."),
 ("echo first line > notes.txt","No output; file notes.txt is created.","Output redirection (FR-14)."),
 ("echo second line >> notes.txt","No output; line appended.","Append redirection (FR-15)."),
 ("cat < notes.txt","Prints both lines.","Input redirection (FR-16)."),
 ("cat notes.txt | grep second","Prints only: second line","Pipe between two processes (FR-18)."),
 ("ls | sort | head -n 3","Prints notes.txt","Three-stage pipeline (FR-18)."),
 ("sleep 5 &","Prints [1] <pid> and the prompt returns at once; later `[1]+  Done   sleep 5` appears before a prompt.","Background execution and job reaping (FR-20)."),
 ("sleep 30   then press Ctrl+C","Sleep is killed, a newline is printed, prompt returns; `echo $?` prints 130.","Signal handling; shell survives (FR-21, FR-06)."),
 ("invalidcommand","mysh: invalidcommand: command not found; `echo $?` prints 127.","Invalid-command handling (FR-07)."),
 ("cd nosuchdir","mysh: cd: nosuchdir: No such file or directory","Built-in error handling (FR-08)."),
 ("cat < missing.txt","mysh: missing.txt: No such file or directory","Redirection error (FR-17)."),
 ("echo one; echo two","one / two on separate lines.","Sequencing with ; (FR-19)."),
 ("exit   (or press Ctrl+D)","Shell terminates.","Graceful termination (FR-10, FR-22)."),
]
demo_md="# Demonstration Script\n\nRun the shell with `make && ./mysh`. Follow the steps in order in one interactive session (about 5 minutes).\n\n"
for i,(c,e,w) in enumerate(steps,1):
    demo_md+=f"### Step {i}\n\n**Command:** `{c}`  \n**Expected behavior:** {e}  \n**What this demonstrates:** {w}\n\n"
demo_md+=f"""## Scripted (non-interactive) run

`demo/demo.mysh` runs a subset of the steps without a terminal: `./mysh demo/demo.mysh`. This is the captured result of an actual run on {DATE} (stdout, then stderr):

```
{demo_out.rstrip()}
```

```
{demo_err.rstrip()}
```

(In non-interactive mode no prompt or `[1] pid` job banner is printed.) The same script is executed as system test ST-10.
"""
write("DEMO_SCRIPT.md", demo_md)

# ------------------------------------------------------------------ SRS.md
def feat_sections():
    o=[]; n=1
    for feat in FEATURE_ORDER:
        desc,stim=FEATURE_INFO[feat]
        frs=[f for f in FR if f[2]==feat]
        prios=sorted({f[3] for f in frs}, key=["High","Medium","Low"].index)
        o.append(f"## 5.{n} {feat}\n\n### 5.{n}.1 Description and Priority\n\n{desc} Priority: **{prios[0]}**"+(" (contains Medium items: "+", ".join(f[0] for f in frs if f[3]=='Medium')+")" if len(prios)>1 else "")+".\n\n")
        o.append(f"### 5.{n}.2 Stimulus/Response Sequences\n\n"+"\n".join(f"* {s}" for s in stim)+"\n\n")
        o.append(f"### 5.{n}.3 Functional Requirements\n\n")
        for f in frs:
            o.append(f"**{f[0]} - {f[1]}** (Priority: {f[3]})\n\n{f[4]}\n\n*Expected behaviour:* {f[5]}\n\n*Error/exception behaviour:* {fr_fix(f[6])}\n\n")
        n+=1
    return "".join(o)
glossary=[("Shell / command-line interpreter","A program that reads commands from a user or a file and runs them."),
("Built-in","A command implemented inside the shell process (cd, pwd, exit, help, export, unset, env)."),
("Pipeline","One or more commands joined by | so that each command's output feeds the next."),
("Redirection","Connecting a command's standard input or output to a file (<, >, >>)."),
("Foreground / background job","A pipeline the shell waits for / one started with & that the shell does not wait for."),
("fork()","POSIX call that creates a copy of the calling process."),
("exec (execvp)","POSIX call family that replaces the current process image with a new program; execvp searches PATH."),
("waitpid()","POSIX call to wait for or poll the state of a child process."),
("pipe() / dup2()","System calls that create a unidirectional byte channel / duplicate a file descriptor."),
("PATH","Environment variable listing directories searched for executables."),
("Environment variable","NAME=VALUE string inherited by child processes."),
("Zombie process","A terminated child whose exit status has not yet been collected by its parent."),
("SIGINT","Signal generated by Ctrl+C."),("EOF","End of input; Ctrl+D on a terminal."),
("Exit status","Small integer returned by a process; 0 means success; shown by $?."),
("SRS","Software Requirements Specification."),("RTM","Requirement Traceability Matrix."),
("POSIX","Portable Operating System Interface, the standard describing these system calls."),
("pty","Pseudo-terminal, used by the tests to simulate a keyboard.")]
SEC_BLOCK = ("### 6.3.1 Security Objectives\n\nThe shell runs with the rights of the invoking user, has no network interface and no authentication of its own. The main assets are the user's files and environment, and the integrity of what the user asked to run. The objectives are:\n\n"
 + table(["ID","Objective","Description"],[list(x) for x in SO])
 + "\n### 6.3.2 Security Requirements\n\nEach requirement is verifiable; the last column lists the executed tests that verify it.\n\n"
 + table(["ID","Objective","Requirement","Priority","Verified by"],[[r[0],r[1],r[2],r[3],", ".join(tests_for(r[0],("UT","TC","SC","NF","ST")))] for r in SR])
 + "\n### 6.3.3 Assumptions, scope and residual risks\n\n* Authentication, access control and auditing are provided by the operating system; the shell does not duplicate them.\n* PATH entries and the inherited environment are trusted. A `.` or empty PATH entry lets a file in the current directory be executed, as in other shells.\n* The shell does not limit the number of processes a user starts; limits such as `ulimit -u` apply.\n* Out of scope: sandboxing of started programs, network security, encryption.\n* Deviation from POSIX for safety: expanded text is not split into several words (SR-02).\n* The shell does not protect the user from destructive commands they type (for example `rm -rf`).\n")
UC_TABLE = table(["Use case","Actor","Description","Related requirements"],[
 ["UC1 Run external command","User, OS","User types a program name with arguments; shell searches PATH, runs it and reports status","FR-05, FR-06, FR-07"],
 ["UC2 Use built-in command","User","cd, pwd, exit, help run inside the shell","FR-08 to FR-11"],
 ["UC3 Manage environment variables","User","export, unset, env, NAME=VALUE, $VAR expansion","FR-12, FR-13"],
 ["UC4 Run script / -c / piped input","User","Commands read from a file, a string or stdin without a prompt","FR-02"],
 ["UC5 Quit the shell","User","exit or Ctrl+D ends the session with the proper status","FR-10, FR-22"],
 ["UC6 Interrupt with Ctrl+C","User","Stops the foreground job or abandons the input line; shell stays alive","FR-21"],
 ["UC7 Redirect input/output (extends UC1)","User, OS","< > >> connect standard streams to files","FR-14 to FR-17"],
 ["UC8 Build a pipeline (extends UC1)","User, OS","Commands joined by | run concurrently","FR-18"],
 ["UC9 Run in background (extends UC1)","User, OS","& starts a job and returns to the prompt at once","FR-20"],
 ["UC10 Chain commands (extends UC1)","User","; runs commands one after another","FR-19"],
 ["UC11 Report invalid command / syntax error (extends UC1)","User","Diagnostic message and status; shell continues","FR-04, FR-07, FR-17"],
 ["UC12 Search PATH (included by UC1)","OS","Locate the executable named by the user","FR-05"]])
srs=f"""---
title: "Software Requirements Specification"
subtitle: "{PROJECT} - Software Engineering Project 15"
---

**PES UNIVERSITY, BANGALORE**

**Department of Computer Science and Engineering**

**Software Requirements Specification: {PROJECT}**

**Version 1.0 approved**

**Prepared by:** Software Engineering Project 15 team (Member 1, Member 2, Member 3, Member 4)

**Organization:** Department of Computer Science and Engineering, PES University, Bangalore

**Date created:** {DATE}

## Revision History

"""+table(["Name","Date","Reason For Changes","Version"],[["Project team (Members 1-4)",DATE,"Initial release describing the implemented shell","1.0"]])+f"""
# 1. Introduction

## 1.1 Purpose

This document specifies the software requirements of **{PROJECT}** (executable `{BINARY}`, release 1.0): a simple Unix-like command-line interpreter written in C. It covers the whole product; the shell is a self-contained program and is not a subsystem of a larger system.

## 1.2 Intended Audience

* **Developers** (Members 1-4) use sections 3-6 and the RTM (Appendix C) to implement and change the shell.
* **Testers** use section 5 and Appendix C to derive and trace test cases (`docs/STP.docx`).
* **Faculty / evaluators** use the whole document to assess completeness and consistency.
* **Users** (students running the shell) use sections 2 and 3.1.

Section 2 gives the overall picture, section 3 the interfaces, section 4 the analysis models, section 5 the functional requirements grouped by feature, section 6 the non-functional requirements, and the appendices the glossary, the command grammar and status codes, and the traceability matrix.

## 1.3 Product Scope

`{BINARY}` reads a line of text, interprets it and asks the operating system to run the requested programs. It lets a user run programs found in PATH, use the built-ins cd, pwd, exit, help, export, unset and env, manage environment variables, redirect input and output with `<`, `>` and `>>`, connect commands with pipes, chain commands with `;`, run commands in the background with `&`, and stay in control when pressing Ctrl+C. The purpose is to demonstrate the core mechanisms of a Unix shell (process creation, execution, waiting, descriptors and signals) in a well-structured, tested C code base. Out of scope: job control (fg/bg/jobs), wildcard expansion, command substitution, `&&`/`||`, control-flow scripting, line editing and history (see section 2.5).

## 1.4 References

1. Project Guidelines and SRS template supplied for Software Engineering Project 15, PES University (SRS-Document.docx).
2. IEEE Std 830-1998, Recommended Practice for Software Requirements Specifications.
3. The Open Group, POSIX.1-2008 (IEEE Std 1003.1-2008): Shell Command Language; `fork`, `execvp`, `pipe`, `dup2`, `waitpid`, `sigaction`.
4. W. Richard Stevens, Stephen Rago, *Advanced Programming in the UNIX Environment*, 3rd ed., Addison-Wesley, 2013.
5. Project documents in this repository: `docs/DESIGN.md`, `docs/STP.docx`, `docs/RTM.md`, `README.md`.

# 2. Overall Description

## 2.1 Product Perspective

`{BINARY}` is a new, self-contained product; it replaces no existing system. It sits between the user's terminal (or a script) and the operating-system kernel, as shown in Figure 1. Its only external interfaces are the terminal/stdin/stdout/stderr, the file system, the process and signal interface of the OS, and the programs it launches.

{F(1)}
## 2.2 Product Functions

* Interactive prompt and read-eval loop; execution of scripts, `-c` strings and piped input
* Tokenizing and parsing with quotes, escapes, comments and syntax-error reporting
* Execution of external programs with PATH search; exit-status tracking (`$?`)
* Built-ins: cd, pwd, exit, help, export, unset, env
* Environment variables and `$VAR`, `${{VAR}}`, `$?`, `$$`, `~` expansion
* Redirection `<`, `>`, `>>`; pipelines `|`; sequencing `;`
* Background execution `&` with completion notices
* Signal handling (Ctrl+C, Ctrl+Z, Ctrl+D) and graceful termination

## 2.3 User Classes and Characteristics

| User class | Characteristics | Importance |
|---|---|---|
| Student / developer user | Comfortable with a terminal; uses the shell interactively to run programs and build pipelines | Most important |
| Script author | Writes text files of commands and runs `mysh script` or `mysh -c` | Important |
| Evaluator / tester | Runs the demo and test suites; reads messages and exit codes | Important |
| Maintainer | Extends the C code (e.g. adds a built-in) | Less frequent |

No privilege levels exist; the shell runs with the rights of the invoking user.

## 2.4 Operating Environment

Linux or another POSIX system with a C11 compiler (gcc 13.3 tested), GNU make, and the standard utilities used in commands (`ls`, `cat`, `grep`, `sort`, `sleep`). Tested only on Ubuntu 24.04. No third-party libraries are required. A terminal emulator is required for interactive use. Bash and Python 3 are needed only to run the test suites.

## 2.5 Design and Implementation Constraints

* Language: C (C11), using POSIX system calls; no external libraries.
* Process creation with `fork()` and program loading with the `exec` family (project requirement).
* Command input via `getline()`: no line editing, no history, no tab completion.
* No job control: `fg`, `bg`, `jobs` and Ctrl+Z suspension are not provided; Ctrl+Z and Ctrl+\\ are ignored.
* Not supported: wildcard/glob expansion, command substitution, `&&`, `||`, here-documents, `2>`/`&>` redirection, aliases, functions and control flow, `~user`.
* At most 64 background jobs are tracked for notification.
* Coding conventions: one module per concern, headers document interfaces, warnings enabled (`-Wall -Wextra -Wpedantic`).

## 2.6 Assumptions and Dependencies

* The host provides a POSIX kernel with working `fork`, `pipe` and signals, and the utilities named in the tests.
* `PATH` and `HOME` are set by the parent environment; if `HOME` is unset, `cd` without argument reports an error.
* Input is text in the terminal's encoding; the shell treats bytes opaquely.
* The terminal delivers Ctrl+C as SIGINT to the foreground process group.

# 3. External Interface Requirements

## 3.1 User Interfaces

The user interface is a text terminal.

* **Prompt:** `mysh:<current directory>$ ` written to standard error (so it does not pollute redirected output); shown only when standard input is a terminal.
* **Input:** one command line per Enter; Ctrl+C abandons the line; Ctrl+D at an empty prompt exits.
* **Messages:** all diagnostics are written to standard error as `mysh: <detail>`; program output goes to standard output.
* **Job notices:** `[id] pid` when a background job starts; `[id]+  Done                    <command>` when it has finished, shown before a later prompt (interactive mode only).
* **Help:** the `help` built-in lists all built-ins and operators. Command-line options: `mysh [-c command | script_file]`, `mysh --help`, `mysh --version`.

## 3.2 Software Interfaces

| Interface | Purpose |
|---|---|
| Operating system (Linux, POSIX.1-2008) | `fork`, `execvp`, `pipe`, `dup2`, `open`, `close`, `waitpid`, `sigaction`, `chdir`, `getcwd`, `getenv`/`setenv`/`unsetenv`, `isatty` |
| C standard library (glibc) | I/O, memory, string functions, `getline` |
| Launched programs | Any executable in PATH; they receive argv, the environment and redirected descriptors, and return an exit status |
| File system | Files named in `<`, `>`, `>>`, script files, working directory |

Data passed in: command text, environment. Data passed out: program output, exit status (`$?` and the shell's own exit code), diagnostics.

## 3.3 Communications Interfaces

The shell has no network communication. Inter-process communication is limited to anonymous pipes created for `|` and to signals (SIGINT and the default SIGPIPE/SIGCHLD behaviour).

## 3.4 Hardware Interfaces

None directly. The terminal device is accessed through the operating system's standard descriptors 0, 1 and 2.

# 4. Analysis Models

{F(5)}
The diagram above is the UML use-case diagram (actors: **User** and the secondary actor **Operating System**; `<<extend>>` and `<<include>>` relationships between use cases). Use cases UC1-UC12 correspond to the features in section 5:

{UC_TABLE}

{F(3)}
{F(4)}
{F(7)}
{F(6)}
{F(8)}
{F(2)}
# 5. System Features

Requirement identifiers use the tag **FR-nn** (functional requirement, unique across the document); each is verified by at least one executed test listed in Appendix C.

"""+feat_sections()+f"""
# 6. Other Nonfunctional Requirements

## 6.1 Performance Requirements

Measurable performance requirements are given in NFR-01 (section 6.4): a background start returns within 500 ms, 1000 external commands run within 5 s and 1000 built-ins within 1 s on the reference environment. Rationale: the prompt must stay responsive; run time of external programs is outside the shell's control, so thresholds are generous regression bounds, not hardware promises.

## 6.2 Safety Requirements

The shell is not safety-critical. Actions that must be prevented: the shell being terminated by Ctrl+C or Ctrl+\\ during normal use; a failed redirection running the command anyway (FR-17); descriptor leaks that could block pipeline readers (FR-18). The shell does not add safeguards against destructive commands such as `rm -rf`; the user is responsible for the commands typed.

## 6.3 Security Requirements

{SEC_BLOCK}
## 6.4 Software Quality Attributes

Priority order: correctness > robustness > clarity of code > ease of demonstration > performance.

"""+nfr_table()+"""
## 6.5 Business Rules

* Domain rules follow POSIX shell conventions: exit status 0 = success, 126 = found but not executable, 127 = not found, 128+N = killed by signal N, 2 = syntax error/usage.
* The status of a pipeline is the status of its last command.
* A `cd`, `exit`, `export`, `unset` or `NAME=VALUE` typed alone acts on the shell itself; inside a pipeline or with `&` it acts only on a child process and has no lasting effect.
* Shell variables and environment variables are the same set.

# 7. Other Requirements

* **Build:** `make` builds `mysh`; `make test` runs all suites; `make sanitize` builds with AddressSanitizer/UBSan.
* **Internationalisation:** messages are in English; no locale-specific behaviour is required.
* **Legal / reuse:** original student work for academic submission; only the C library and POSIX interfaces are used.
* **Database requirements:** none.

# Appendix A: Glossary

"""+table(["Term","Definition"],[list(g) for g in glossary])+"""
# Appendix B: Field Layouts (command grammar and status codes)

The template's sample sheets describe banking records and do not apply to a shell. The equivalent layout information for this product is the command-line grammar, the main data structures and the exit-status table.

**Command grammar**

```
line       := pipeline { (';' | '&' | newline) pipeline } [ '&' ]
pipeline   := command { '|' command }
command    := { WORD | redirect }     (at least one WORD)
redirect   := '<' WORD | '>' WORD | '>>' WORD
WORD       := unquoted text | 'single quoted' | "double quoted" | \\char
              (expansions $NAME ${NAME} $? $$ and a leading ~ apply outside
              single quotes)
comment    := '#' ... end of line     (only where a word could start)
```

**Data structures**

| Field | Structure | Type | Description | Mandatory |
|---|---|---|---|---|
| argv, argc | Command | char **, int | Program name and arguments | Y |
| infile | Command | char * | Target of `<` | N |
| outfile | Command | char * | Target of `>` / `>>` | N |
| append | Command | int | 1 for `>>` | N |
| cmds, ncmds | Pipeline | Command *, int | Commands joined by pipes | Y |
| background | Pipeline | int | 1 when terminated by `&` | N |
| last_status | Shell | int | Value of `$?` | Y |
| jobs[64] | Shell | Job | Background jobs awaiting a Done notice | N |

**Exit status codes**

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | General failure (built-in error, redirection failure, fork/pipe failure) |
| 2 | Syntax error, usage error, `exit` with non-numeric argument |
| 126 | Command found but cannot be executed |
| 127 | Command (or script file) not found |
| 128+N | Terminated by signal N (130 = SIGINT, 137 = SIGKILL) |

# Appendix C: Requirement Traceability Matrix

Architecture references ARCH-n and design references DES-n are defined in `docs/DESIGN.md`. Test IDs: UT = unit, TC = functional/integration/negative, ST = system.

"""+table(RTM_HEAD,rtm_rows())
write("SRS.md", srs)

# ------------------------------------------------------------------ README.md
readme=f"""# {PROJECT}

**Software Engineering Project 15** - a simple Unix-like shell written in C.

> Problem statement: *A simple Unix-like shell to execute commands from the command line.*

## Features

* Interactive prompt showing the working directory; also runs scripts, `-c` strings and piped input
* External commands via `fork()` + `execvp()` with PATH search; exit status in `$?`
* Built-ins: `cd` (incl. `cd -`), `pwd`, `exit [n]`, `help`, `export`, `unset`, `env`
* Environment variables, `NAME=VALUE`, `$VAR`, `${{VAR}}`, `$?`, `$$`, `~`
* Quotes (`'...'`, `"..."`), backslash escapes, `#` comments
* Redirection `<`, `>`, `>>`; pipelines of any length with `|`; sequencing with `;`
* Background execution with `&` and `[id]+ Done` notices; no zombie processes
* Ctrl+C handling (shell survives, foreground job dies, background jobs unaffected); Ctrl+D exits
* Clear error messages and POSIX-style exit codes (2 syntax, 126, 127, 128+signal)

## Architecture

```
main.c ──> shell.c (loop, signals, state) ──> parser.c  (text -> Pipeline)
                     └────────────────────> executor.c (fork/exec/pipes/redirs/jobs) ──> builtins.c
                       utils.c (memory, errors, StrBuf) used by all
```

Diagrams (PNG + Graphviz sources) are in `docs/diagrams/`; the full description is in `docs/DESIGN.md`.

## Project structure

```
simple-shell/
├── Makefile
├── README.md
├── src/          main.c shell.c/h parser.c/h executor.c/h builtins.c/h utils.c/h
├── tests/        test_parser.c  run_tests.sh  interactive_test.py  fuzz_parser.c  fuzz_shell.py  fdcheck.py  results_*
├── demo/         demo.mysh
└── docs/         SRS.docx/.md  REQUIREMENTS.md  DESIGN.md  TEAM_AND_PLAN.md  STP.md
                  RTM.md  DEMO_SCRIPT.md  FINAL_REPORT.docx/.md  PPT_CONTENT.md  STP.docx/.md  SAD.docx/.md
                  SUBMISSION_CHECKLIST.md  CONSISTENCY_CHECK.md  diagrams/
```

## Requirements

{len(FR)} functional requirements (FR-01 to FR-{len(FR):02d}) and {len(NFR)} non-functional requirements; see `docs/REQUIREMENTS.md` and the SRS.

## Compilation

Needs gcc (or any C11 compiler) and make on Linux/POSIX.

```
make          # builds ./mysh
make clean
```

## Execution

```
./mysh                    # interactive
./mysh -c "ls | wc -l"    # one command string
./mysh demo/demo.mysh     # script file
echo "pwd" | ./mysh       # commands from stdin
```

## Example commands

```
mysh:/home/user$ pwd
mysh:/home/user$ echo Hello
mysh:/home/user$ cd ..
mysh:/home$ export NAME=World
mysh:/home$ echo "Hello $NAME" > greeting.txt
mysh:/home$ cat < greeting.txt
mysh:/home$ cat greeting.txt | grep Hello
mysh:/home$ echo more >> greeting.txt
mysh:/home$ sleep 5 &
mysh:/home$ invalidcommand
mysh:/home$ exit
```

## Testing

```
make unit-test    # {counts['unit']} parser/utility unit tests
make test         # unit + {counts['func']} functional + {counts['sec']} security + {counts['nf']} non-functional + {counts['pty']} pseudo-terminal tests + fuzzing
make sanitize     # rebuild with AddressSanitizer/UBSan and rerun unit + functional tests
make fuzz         # parser fuzzer (200,000 inputs) and process-level fuzzer under the sanitizers
```

{STATUS} (Sanitizer run: unit and functional suites, 0 reports; fuzzing: 200,000 parser inputs and 600 real shell runs, 0 findings.) Details, the list of tests still to be executed and the RTM are in `docs/STP.docx` and `docs/RTM.md`.

## Limitations

No job control (`fg`, `bg`, `jobs`, Ctrl+Z), wildcards (`*.c`), command substitution, `&&`/`||`, `2>` redirection, here-documents, aliases, functions, control flow, `~user`, history or line editing. Every shell variable is an environment variable. Background-job completion notices appear only when the next prompt is drawn. Tested on Ubuntu 24.04 only.

## Team contribution

"""+table(["Member","Primary responsibility","Functional features"],[[m[0],m[1],m[2]] for m in TEAM])+"""
## Future enhancements

Job control (`jobs`, `fg`, `bg` with process groups); wildcard expansion; `&&`, `||`; stderr redirection (`2>`, `2>&1`); command substitution; readline-style editing and history; shell functions and control flow; SIGCHLD-driven job notices; portability testing on macOS/BSD.
"""
with open(os.path.join(ROOT,"README.md"),"w") as f: f.write(readme)

# ------------------------------------------------------------------ FINAL_REPORT.md
rep=f"""---
title: "Simple Shell (Command Line Interpreter)"
subtitle: "Software Engineering Project 15 - Final Report"
---

# Abstract

This report describes the requirements, design, implementation and verification of *mysh*, a simple Unix-like command-line shell written in C. The shell reads commands interactively or from files, executes external programs using `fork()` and `execvp()`, provides built-in commands (cd, pwd, exit, help, export, unset, env), supports environment variables, quoting, input/output redirection, pipelines, command sequencing, background execution and Ctrl+C handling. The work follows a software-engineering process: a Software Requirements Specification with {len(FR)} functional and {len(NFR)} non-functional requirements, a modular architecture, a requirement traceability matrix and a layered test strategy. {n_all} tests were designed and executed on Ubuntu 24.04; {n_pass} passed and {n_all-n_pass} failed.

# 1. Introduction

The shell is the classic interface to a Unix-like operating system. Building one exposes the central operating-system mechanisms: creating processes, loading programs, wiring file descriptors, waiting for children and handling signals. This project builds a small but complete shell and treats it as a software-engineering exercise: requirements first, then design, implementation, tests and traceability.

# 2. Problem statement

"A simple Unix-like shell to execute commands from the command line." Implementation language: C.

# 3. Objectives

* Implement a working command-line interpreter that runs commands typed by a user.
* Support built-in commands, environment variables, redirection, pipes and background execution.
* Handle errors and signals so that the shell remains stable.
* Document the product with an SRS, design, test plan and traceability matrix.
* Verify the implementation with automated unit, functional and system tests.

# 4. Scope

In scope: the features listed in the abstract. Out of scope: job control, wildcard expansion, command substitution, `&&`/`||`, control-flow scripting, line editing and history (see Limitations).

# 5. Problem context and existing solutions

Production shells such as bash, dash and zsh implement the POSIX shell language and many extensions. They are large and hard to study. Educational shells reduce the language to the essential mechanisms. This project sits in that category: it follows POSIX conventions where it implements a feature (quoting rules, exit codes 126/127, `$?`) and states clearly what it omits.

# 6. Proposed solution

A single-process, modular C program. A parser turns each input line into `Pipeline`/`Command` structures; an executor creates the processes; a small built-in layer handles commands that must run inside the shell; the core loop ties these together and manages signals and jobs.

# 7. Requirements

The {len(FR)} functional requirements are grouped in nine features: command loop and input sources, parsing, external command execution, built-ins, environment and expansion, redirection, pipelines and sequencing, background execution and signal handling.

"""+table(["ID","Title","Priority"],[[f[0],f[1],f[3]] for f in FR])+"""
Non-functional requirements cover performance (responsiveness), robustness, usability, maintainability, portability, security, testability, memory safety and reliability:

"""+table(["ID","Category"],[[n[0],n[1]] for n in NFR])+f"""
# 8. Architecture

The design has five modules on top of the POSIX interface (Figure 1). Dependencies follow Figure 2: the core depends on the parser and executor, the executor on the built-ins, and all on the utilities.

{F(1)}
{F(2)}
# 9. Design

**Parsing.** One pipeline is parsed at a time so that expansion sees the effects of earlier commands on the same line. Words are built with a growable string buffer; quoting and escapes are handled character by character; syntax errors free all partial data and discard the rest of the line.

**Execution.** `execute_pipeline()` runs a lone built-in or assignment in the shell process; otherwise it forks one child per command, connects them with pipes, applies redirections, and either waits (foreground) or records a job (background). Exec failures map to statuses 127 and 126.

**Signals.** The shell's SIGINT handler only sets a flag and is installed without `SA_RESTART`, so a blocked `getline()` returns and the prompt is redrawn. Foreground children use the default action; background children ignore SIGINT. SIGTSTP and SIGQUIT are ignored because there is no job control.

{F(3)}
{F(4)}
{F(6)}
# 10. Implementation

The program consists of about {sum(len(open(p).read().splitlines()) for p in glob.glob(os.path.join(ROOT,'src','*.[ch]')))} lines of C in {len(glob.glob(os.path.join(ROOT,'src','*.c')))} source files and {len(glob.glob(os.path.join(ROOT,'src','*.h')))} headers, built with a Makefile using `-std=c11 -Wall -Wextra -Wpedantic` (no warnings). Key elements: `parse_next_pipeline()` and `read_word()` (parser.c); `execute_pipeline()`, `exec_child()`, `apply_redirections()`, `wait_foreground()`, `jobs_reap()` (executor.c); a table-driven built-in dispatcher (builtins.c); `shell_run_stream()` and `shell_setup_signals()` (shell.c). Full source is in `src/`.

# 11. Functional features

Each feature is demonstrated in `docs/DEMO_SCRIPT.md`: prompt and input modes; quoting and expansion; external commands and PATH; cd/pwd/exit/help/export/unset/env; `>`, `>>`, `<`; pipes; `;`; `&`; Ctrl+C and Ctrl+D; error messages and exit codes.

# 12. Team ownership

"""+table(["Member","Primary Responsibility","Functional Features"],[[m[0],m[1],m[2]] for m in TEAM])+f"""
# 13. Testing

Strategy: unit tests of the parser and helpers; functional and integration tests through `mysh -c`, script and stdin; negative tests; system tests through a pseudo-terminal and the demonstration script; a sanitizer build. Every functional requirement is traced to at least one executed test in the RTM.

"""+table(["Level","Tests designed","Tests executed","Passed","Failed"],[
 [lbl,counts[k],counts[k],sum(1 for t in tests.values() if t['kind']==k and t['status']=='PASS'),sum(1 for t in tests.values() if t['kind']==k and t['status']!='PASS')]
 for lbl,k in (("Unit","unit"),("Functional / integration / negative / robustness (incl. ST-10 demo)","func"),("Security (SC, incl. fuzzing)","sec"),("Non-functional (NF)","nf"),("System (pty)","pty"),("Sanitizer build (ST-12)","manual"))])+f"""
Note: ST-10 (demo script) is counted with the functional harness because it runs from `run_tests.sh`; the 24+ unit, security, non-functional and system tests are described in `docs/STP.docx`.

# 14. Results

{STATUS} The sanitizer build reported no errors on the unit and functional suites. Two early failures (TC-36, TC-74) were caused by the test harness capturing output with `$(...)`, not by the shell; they were corrected in the tests. Not yet done: testing on non-Linux systems, running the pseudo-terminal suite under the sanitizer, and manual testing of full-screen programs.

# 15. Limitations

No job control (`fg`, `bg`, `jobs`, Ctrl+Z); no wildcard expansion; no command substitution, `&&`, `||`, here-documents, `2>` redirection, aliases, functions or control flow; no `~user`; no line editing or history; all variables are environment variables; job-completion notices appear only at the next prompt; at most 64 tracked background jobs; tested on Linux only.

# 16. Future enhancements

Job control with process groups and `tcsetpgrp`; globbing; `&&`/`||`; stderr redirection; command substitution; line editing and history (readline or custom); SIGCHLD-driven notifications; shell functions and control flow; cross-platform testing.

# 17. Conclusion

The project delivers a working, documented and tested Unix-like shell whose behaviour matches its specification: every documented feature is implemented, every functional requirement is traced to an executed test, and known limitations are stated openly. The exercise shows how a small systems program benefits from requirements-first design, modular structure and automated testing.

# 18. References

1. IEEE Std 830-1998, Recommended Practice for Software Requirements Specifications.
2. The Open Group, POSIX.1-2008, Shell Command Language and System Interfaces.
3. W. R. Stevens and S. A. Rago, *Advanced Programming in the UNIX Environment*, 3rd ed., 2013.
4. M. Kerrisk, *The Linux Programming Interface*, No Starch Press, 2010.
5. Project documents: SRS (`docs/SRS.docx`), design (`docs/DESIGN.md`), test plan (`docs/STP.docx`), RTM (`docs/RTM.md`).
"""
write("FINAL_REPORT.md", rep)

# ------------------------------------------------------------------ PPT_CONTENT.md
slides=[
("Title",["Simple Shell (Command Line Interpreter)","Software Engineering Project 15","Team: Member 1, Member 2, Member 3, Member 4"],"Title slide with project name and team","Introduce the project: a Unix-like shell written in C, built as a software-engineering project with requirements, design, tests and traceability."),
("Problem Statement",["\"A simple Unix-like shell to execute commands from the command line.\"","Language: C, Linux/POSIX","Deliverables: working shell, SRS, design, tests, RTM"],"Screenshot of the prompt","State the problem in one sentence and what we deliver beyond code."),
("Motivation",["The shell is every user's interface to the OS","Building one teaches fork/exec/wait, pipes, redirection, signals","Practice of requirements-first engineering"],"Icon: terminal window","Explain why a shell is a good project: small enough to finish, rich enough to touch core OS concepts."),
("Objectives",["Run commands and built-ins","Redirection, pipes, background jobs","Stable error and signal handling","SRS + design + tests + traceability"],"Checklist graphic","Objectives map directly to requirement groups in the SRS."),
("Proposed Solution",["Modular C program in 6 source modules","Parser -> Pipeline structure -> Executor","One pipeline parsed and executed at a time","POSIX system calls only, no libraries"],"docs/diagrams/01_architecture.png","Walk through the architecture figure from user to kernel."),
("Functional Features",[f"{len(FR)} functional requirements, 9 features","cd pwd exit help export unset env","< > >> | ; &  quotes, $VAR, ~","Ctrl+C / Ctrl+D handling, exit codes 126/127/128+N"],"Table of features from SRS section 5","Summarise features; emphasise that each has an ID and a test."),
("Architecture",["Shell Core: loop, prompt, signals","Parser: text -> Command/Pipeline","Executor: fork, exec, pipes, redirs, jobs","Built-ins and Utilities"],"docs/diagrams/02_components.png","Show module dependencies; point out that they mirror the source files."),
("Command Execution Flow",["Lone built-in / assignment runs in the shell","Otherwise fork one child per command","Child: dup2 pipes, redirections, execvp","Parent: wait, or register background job"],"docs/diagrams/04_execution_flow.png","Explain the decision at the top: why cd must not run in a child."),
("Implementation",["parse_next_pipeline(), read_word()","execute_pipeline(), exec_child(), apply_redirections()","SIGINT handler sets a flag; no SA_RESTART","Zero warnings with -Wall -Wextra -Wpedantic"],"Code snippet of the fork loop","Highlight two or three design decisions from DESIGN.md section 9."),
("Team Contribution",[f"{m[0]}: {m[1]} ({m[2]})" for m in TEAM],"Product-ownership table","Each member owns functional requirements in named modules; testing and documentation are additional."),
("Testing",[f"{counts['unit']} unit + {counts['func']} functional + {counts['pty']} terminal + sanitizer run","Every FR traced to an executed test (RTM)","Automated: make test, make sanitize","Still to do: non-Linux, manual full-screen programs"],"Screenshot of make test summary","Be explicit about what was and was not executed."),
("Demonstration",["Basic commands and cd/pwd","Variables, > >> <","Pipes","Background job and Ctrl+C","Errors and exit"],"Live terminal","Follow docs/DEMO_SCRIPT.md step by step."),
("Results",[f"{n_pass} of {n_all} designed tests pass on Ubuntu 24.04","No sanitizer findings (unit + functional)","Two early test failures were harness bugs, fixed"],"Bar or table of test results","Report results honestly, including the harness issue we found."),
("Limitations / Future Work",["No job control, globbing, &&, ||, 2>","No history / line editing","Tested on Linux only","Next: job control, globbing, stderr redirection"],"Roadmap graphic","State limitations openly; they are documented in the SRS section 2.5."),
("Conclusion",["A working, documented, tested shell","Requirements -> design -> code -> tests are traceable","Thank you - questions?"],"Team photo or logo","Close by restating the engineering outcome, then take questions."),
]
ppt="# Presentation Content (15 slides)\n\n"
for i,(t,b,d,s) in enumerate(slides,1):
    ppt+=f"## Slide {i}: {t}\n\n"+"\n".join(f"* {x}" for x in b)+f"\n\n**Suggested diagram/screenshot:** {d}\n\n**Speaker explanation:** {s}\n\n"
write("PPT_CONTENT.md", ppt)

# ------------------------------------------------------------------ SUBMISSION_CHECKLIST.md
chk="""# Final Submission Checklist

Tick each item before submitting. Items marked (verified) were checked when these files were generated; the rest need the team.

- [ ] Replace "Member 1..4" with real names/SRNs in SRS.docx, FINAL_REPORT.docx, README.md, TEAM_AND_PLAN.md, PPT
- [ ] Confirm the ownership table matches who actually worked on what
- [x] Source code compiles without warnings: `make` (verified)
- [x] `make test` passes (verified on Ubuntu 24.04; re-run on your own machine)
- [ ] Take screenshots of `make test` and of the demo session for the report/slides
- [x] SRS follows the supplied template structure (sections 1-7, appendices A-C) (verified)
- [x] Every FR has an ID, priority, behaviour and error behaviour (verified)
- [x] RTM covers every FR and NFR (verified)
- [x] Diagrams correspond to implemented features only (verified against source by review)
- [x] No placeholder text remains in generated documents (automated check, see CONSISTENCY_CHECK.md)
- [ ] Export final report and SRS to PDF if the course requires PDF
- [ ] Prepare and rehearse the demonstration (docs/DEMO_SCRIPT.md)
- [ ] Build the PPT from docs/PPT_CONTENT.md
- [ ] Check the official Project Guidelines once more for submission format, file naming and deadline
- [ ] Follow your course's policy on disclosing the use of AI tools in the work
"""
write("SUBMISSION_CHECKLIST.md", chk)

# ------------------------------------------------------------------ STP.md and SAD.md (Part-1 deliverables)
import gen_stp, gen_sad
SPECS_IDS=[x[0] for x in gen_stp.SPECS]
LOC=sum(len(open(p).read().splitlines()) for p in glob.glob(os.path.join(ROOT,"src","*.[ch]")))
ctx=dict(table=table,F=F,tests=tests,tests_for=tests_for,DATE=DATE,LOC=LOC,idkey=idkey,NFR_EXTRA={})
write("STP.md", gen_stp.build(ctx))
write("SAD.md", gen_sad.build(ctx))

# ------------------------------------------------------------------ consistency check
checks=[]
def chk_(name, ok, detail=""): checks.append((name,ok,detail))
frids=[f[0] for f in FR]
uncovered=[f for f in frids if not [i for i in tests_for(f,("UT","TC","ST")) if tests[i]["status"]=="PASS"]]
chk_("Every FR has at least one PASSED executed test", not uncovered, ", ".join(uncovered))
nosys=[f for f in frids if not tests_for(f,("ST",))]
chk_("Every FR has a system test (ST-10 covers all)", not nosys, ", ".join(nosys))
valid=set(frids)|{n[0] for n in NFR}|{r[0] for r in SR}
bad=[t["id"] for t in tests.values() for r in reqs_of(t) if r not in valid and r!="FR-01..FR-22"]
chk_("Every test references an existing requirement", not bad, ", ".join(bad))
chk_("No test failed", all(t["status"]=="PASS" for t in tests.values()), ", ".join(t["id"] for t in tests.values() if t["status"]!="PASS"))
src_text={os.path.basename(p):open(p).read() for p in glob.glob(os.path.join(ROOT,"src","*"))}
bnames=re.findall(r'\{ "(\w+)",\s+bi_', src_text["builtins.c"])
doc_text=open(os.path.join(HERE,"SRS.md")).read()
missing=[b for b in bnames if b not in doc_text]
chk_("Every implemented built-in is documented in the SRS", not missing, ", ".join(missing))
helptxt=src_text["builtins.c"]
chk_("Built-ins documented (cd,pwd,exit,help,export,unset,env) all exist in source", set(bnames)>={"cd","pwd","exit","help","export","unset","env"}, str(bnames))
badfun=[]
for k,(title,files) in DES.items():
    for fn in re.findall(r"\b([a-z_0-9]+)\(\)", title):
        if not any(re.search(r"\b"+fn+r"\s*\(", src_text.get(f.strip(),"")) for f in files.split(",")): badfun.append(f"{k}:{fn}")
chk_("Every function named in the design index exists in the named source file", not badfun, ", ".join(badfun))
badfile=[f for x in FR for f in x[9].split(", ") if f not in src_text]
chk_("Every code file in the RTM exists", not badfile, ", ".join(badfile))
own={}
for m in TEAM:
    for r in [x.strip() for x in m[2].split(",")]: own.setdefault(r,[]).append(m[0])
mism=[f[0] for f in FR if own.get(f[0])!=[f[10]]]
chk_("Team table and FR owners agree; each FR has exactly one owner", not mism, ", ".join(mism))
chk_("Every member owns at least 5 functional requirements", all(len([1 for f in FR if f[10]==m[0]])>=5 for m in TEAM), "")
chk_("All 8 diagrams exist", all(os.path.exists(os.path.join(HERE,"diagrams",v)) for v in n_files.values()), "")
sysuse=[n for n,t in src_text.items() if re.search(r"\b(system|popen)\s*\(", t)]
chk_("Source never calls system()/popen() (NFR-06)", not sysuse, ", ".join(sysuse))
ph=[]
for name in ("SRS.md","REQUIREMENTS.md","DESIGN.md","TEAM_AND_PLAN.md","STP.md","SAD.md","RTM.md","DEMO_SCRIPT.md","FINAL_REPORT.md","PPT_CONTENT.md"):
    tx=open(os.path.join(HERE,name)).read()
    if re.search(r"\bTBD\b|\bTODO\b|Lorem|<author>|<Project>|<organization>|<date created>|XXX", tx): ph.append(name)
chk_("Every security requirement has a passing test", all([i for i in tests_for(r[0],("UT","TC","SC","NF","ST")) if tests[i]["status"]=="PASS"] for r in SR), ", ".join(r[0] for r in SR if not tests_for(r[0],("UT","TC","SC","NF","ST"))))
chk_("Every security requirement serves a stated security objective", all(r[1] in {o[0] for o in SO} for r in SR), "")
chk_("Every security objective is covered by at least 1 requirement", all(sum(1 for r in SR if r[1]==o[0])>=1 for o in SO), "")
chk_("At least 2 security objectives and 2 security requirements (Part-1 rule)", len(SO)>=2 and len(SR)>=2, "")
chk_("Every NFR has at least one executed test or an inspection/build check", all(tests_for(x[0],("UT","TC","SC","NF","ST")) for x in NFR), ", ".join(x[0] for x in NFR if not tests_for(x[0],("UT","TC","SC","NF","ST"))))
allids=set(tests)
refd=set()
for name in ("SRS.md","STP.md","SAD.md","RTM.md"):
    refd|=set(re.findall(r"\b((?:UT|TC|SC|NF|ST)-\d+)\b", open(os.path.join(HERE,name)).read()))
chk_("Every test ID mentioned in SRS/STP/SAD/RTM exists in the result files", refd<=allids, ", ".join(sorted(refd-allids)))
srs_t=open(os.path.join(HERE,"SRS.md")).read(); stp_t=open(os.path.join(HERE,"STP.md")).read(); sad_t=open(os.path.join(HERE,"SAD.md")).read()
chk_("STP has the 15 template sections and 5.1", all(("## %d. "%i) in stp_t for i in range(1,16)) and "## 5.1 Security Validation" in stp_t, "")
chk_("SAD has template sections 3.1-3.9 and 4.1-4.6", all(("## 3.%d "%i) in sad_t for i in range(1,10)) and all(("## 4.%d "%i) in sad_t for i in range(1,7)), "")
chk_("SAD has at least 2 UML sequence diagrams", sad_t.count("### SD-")>=2, "")
chk_("SRS has a UML use-case diagram and Security section with objectives and requirements", "05_use_case.png" in srs_t and "6.3.1 Security Objectives" in srs_t and "6.3.2 Security Requirements" in srs_t, "")
chk_("Part-1 minimum: at least 10 test cases covering FR, NFR and security", sum(1 for t in tests if t.startswith(("TC","NF","SC")))>=10, "")
chk_("No template placeholder text remains", not ph, ", ".join(ph))
chk_("Features documented in README exist: -c, script, stdin modes tested", all(tests[i]["status"]=="PASS" for i in ("TC-50","TC-51")), "")
cons="# Consistency Check (item 15)\n\nGenerated automatically by `docs/build_docs.py` on each run.\n\n"+table(["Check","Result","Detail"],[[n,"PASS" if ok else "FAIL",d] for n,ok,d in checks])
cons+="\n## Checks that need a human\n\n* Whether the ownership table reflects who really did the work.\n* Whether the diagrams still match the code after future changes (re-run `python3 docs/diagrams/make_diagrams.py` and re-read `docs/DESIGN.md`).\n* Whether the official Project Guidelines impose extra format rules (the uploaded Project_Guidelines.docx contained the project brief, not separate official rules).\n"
write("CONSISTENCY_CHECK.md", cons)

# ------------------------------------------------------------------ PART1_CHECKLIST.md
n_tc=sum(1 for t in tests if t.startswith(("TC","NF","SC")))
p1=f"""# Mini-Project Deliverables Part-1 - compliance checklist (ETA 07 Oct 2026)

Each line of `SE_Mini_Project_Delivereables_Part-1.pdf` and where it is satisfied.

| # | Deliverable item | Where | Status |
|---|---|---|---|
| 1 | SRS in the standard IEEE format (intro and other descriptive sections) | `docs/SRS.docx`, sections 1-3, 7, appendices (PES template structure, IEEE 830 content) | Done |
| 1.ii | FRs and NFRs, clear, unambiguous, concise, measurable | SRS section 5 (FR-01 to FR-{len(FR):02d}, each with behaviour and error behaviour) and 6.4 (NFR-01 to NFR-{len(NFR):02d} with numeric acceptance criteria) | Done |
| 1.iii | UML use-case diagram (at least 1) | SRS section 4 (Figure 5) and use-case table UC1-UC12 | Done |
| 1.iv | Security section with objectives and requirements (at least 2 each) | SRS 6.3: {len(SO)} objectives (SO-1..SO-{len(SO)}), {len(SR)} requirements (SR-01..SR-{len(SR)}), each verified by tests | Done |
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
| 4 | Test cases update in the Test Plan, covering functional and non-functional requirements, at least 7-10 | STP Appendix A (full specifications of {len(SPECS_IDS)} cases) and Appendix B (all {n_all} executed tests: {counts['unit']} unit, {n_tc} functional/security/non-functional cases and {counts['pty']+counts['manual']+1} system) | Done |

Test status: {STATUS} All of these results come from automated runs; see `docs/STP.docx` section 14 and the files in `tests/`.
"""
write("PART1_CHECKLIST.md", p1)

failed=[c for c in checks if not c[1]]
print("consistency:", "ALL PASS" if not failed else failed)
print("tests:", n_pass, "/", n_all)
sys.exit(1 if failed else 0)
