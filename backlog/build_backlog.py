#!/usr/bin/env python3
"""Generate the product backlog (CSV + JSON for GitHub issues) and docs/SPRINT_PLAN.md from the SRS data.
Run from the repo root:  python3 backlog/build_backlog.py
Source of truth: docs/docdata.py (FR / NFR / SR), docs/RTM.md (tests and code files per requirement)."""
import csv, json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "docs"))
import docdata as D

SCALE = [1, 2, 3, 5, 8, 13]
SPRINTS = {0: ("Sprint 0 (dry run)", "2026-10-12", "2026-10-16"), 1: ("Sprint 1", "2026-10-19", "2026-10-23"), 2: ("Sprint 2", "2026-10-26", "2026-10-30")}
MEMBERS = ["Member 1", "Member 2", "Member 3", "Member 4"]

# ---- RTM lookup: requirement -> (tests, system tests, files)
rtm = {}
for line in open(os.path.join(ROOT, "docs", "RTM.md")):
    c = [x.strip() for x in line.strip().strip("|").split("|")]
    if len(c) == 8 and re.match(r"^(FR|NFR|SR)-\d+$", c[1]):
        rtm[c[1]] = dict(tests=c[6], systests=c[7], files=c[5])

SO_TXT = {s[0]: s[1] for s in D.SO}

# id, sprint, owner, points, "so that" clause  (FR stories: sprint/owner/points chosen to balance load)
FR_PLAN = {
 "FR-01": (1, "Member 1", 5, "I can type commands and see results one after another"),
 "FR-02": (1, "Member 1", 3, "I can automate commands from a script, a string or a pipe"),
 "FR-03": (1, "Member 2", 8, "arguments with spaces, quotes and operators are understood correctly"),
 "FR-04": (1, "Member 4", 5, "mistakes in my command line are explained instead of crashing the shell"),
 "FR-05": (1, "Member 1", 5, "I can run any installed program"),
 "FR-06": (1, "Member 1", 3, "commands finish before the next prompt and I can check their status"),
 "FR-07": (1, "Member 4", 3, "I know when a command does not exist or cannot be run"),
 "FR-08": (1, "Member 2", 3, "I can move around the directory tree"),
 "FR-09": (1, "Member 2", 1, "I can see where I am"),
 "FR-10": (1, "Member 4", 2, "I can leave the shell with a chosen status"),
 "FR-11": (1, "Member 4", 2, "I can discover the available built-ins"),
 "FR-12": (2, "Member 2", 5, "programs I start can see my settings"),
 "FR-13": (2, "Member 2", 5, "I can reuse values in later commands"),
 "FR-14": (1, "Member 3", 3, "I can save command output to a file"),
 "FR-15": (1, "Member 3", 2, "I can add output to an existing file"),
 "FR-16": (1, "Member 3", 2, "I can feed a file to a command"),
 "FR-17": (1, "Member 4", 3, "a bad file name never runs the command or crashes the shell"),
 "FR-18": (2, "Member 3", 8, "I can combine small programs into larger tasks"),
 "FR-19": (1, "Member 1", 2, "I can type several commands on one line"),
 "FR-20": (2, "Member 3", 5, "I can keep working while a long job runs"),
 "FR-21": (2, "Member 3", 5, "Ctrl+C stops a runaway job without closing my shell"),
 "FR-22": (1, "Member 1", 2, "the shell ends cleanly and returns the right status"),
}
NFR_PLAN = {"NFR-01": (2, "Member 1", 3), "NFR-02": (2, "Member 4", 3), "NFR-03": (2, "Member 4", 2), "NFR-04": (2, "Member 1", 2),
            "NFR-05": (2, "Member 1", 2), "NFR-06": (2, "Member 4", 3), "NFR-07": (2, "Member 1", 2), "NFR-08": (2, "Member 4", 3),
            "NFR-09": (2, "Member 2", 2)}
SR_PLAN = {"SR-01": (2, "Member 2", 3), "SR-02": (2, "Member 2", 2), "SR-03": (2, "Member 1", 1), "SR-04": (2, "Member 1", 1),
           "SR-05": (2, "Member 1", 2), "SR-06": (2, "Member 4", 5), "SR-07": (2, "Member 2", 2), "SR-08": (2, "Member 3", 3),
           "SR-09": (2, "Member 4", 2), "SR-10": (2, "Member 3", 2)}
# chores: id, title, sprint, owner, points, component, description, acceptance
CHORES = [
 ("CH-01", "Create the GitHub repository and push the project skeleton", 0, "Member 4", 2, "build", "Create the repo, push README, Makefile and src/ layout, add team members as collaborators.", ["Repo exists with README and Makefile on main", "All four members have write access; one repo owner is named in backlog/team.json"]),
 ("CH-02", "Create the GitHub Project board and link it to the repo", 0, "Member 1", 2, "build", "Create a GitHub Project (v2), add fields Story Points and Sprint, link it to the repo (Part-2 item 1a).", ["Project is linked from the repo's Projects tab", "Views: Backlog, Sprint board (Todo / In progress / In review / Done)"]),
 ("CH-03", "Import the backlog as labelled, assigned, pointed issues", 0, "Member 4", 3, "build", "Run scripts/setup_github.sh to create labels, milestones and one issue per backlog item, add them to the Project (Part-2 items 1b-1e).", ["Every FR, NFR and SR has an issue", "Each issue has story points, an assignee, a sprint milestone and links to its tests"]),
 ("CH-04", "Add PR template, CODEOWNERS and branch rules", 0, "Member 2", 1, "build", "Practice PR: add .github/PULL_REQUEST_TEMPLATE.md and CODEOWNERS; repo owner reviews and merges.", ["PR raised by the assignee", "Repo owner approved and merged", "CI is green"]),
 ("CH-05", "Dry run: every member raises one practice PR", 0, "Member 3", 1, "docs", "Each member adds a line to docs/TEAM.md on a branch and raises a PR that closes a practice issue.", ["Four merged PRs, each linked to an issue"]),
 ("CH-06", "Dry run: record a 30-second practice screen capture", 0, "Member 1", 1, "docs", "Practise recording the terminal demo and uploading it to videos/.", ["A practice video exists locally and the upload method (git LFS or release asset) is decided"]),
 ("CH-07", "Enable GitHub Actions: build, tests, sanitizer, PR checks", 1, "Member 3", 3, "build", "Add .github/workflows (ci.yml, pr-hygiene.yml, labeler.yml); require the CI check before merge (Part-2 item 2b).", ["CI runs on every push and PR", "Failing tests block the merge", "Test result files are uploaded as an artifact"]),
 ("CH-08", "Parser unit-test suite (UT-01 to UT-24) in the repo", 1, "Member 2", 3, "tests", "Commit tests/test_parser.c and make unit-test.", ["make unit-test passes locally and in CI"]),
 ("CH-09", "Functional test harness (run_tests.sh) for sprint-1 features", 1, "Member 3", 5, "tests", "Commit tests/run_tests.sh with the fixtures and result files.", ["Harness runs the sprint-1 test cases and writes tests/results_functional.*"]),
 ("CH-10", "Utilities module and uniform error format (utils.c/h)", 1, "Member 4", 3, "utils", "xmalloc, shell_error, StrBuf, name validation, used by every module (design DES-21, NFR-03).", ["All diagnostics start with 'mysh: '"]),
 ("CH-11", "Record and upload the Sprint-1 video (1 minute)", 1, "Member 4", 2, "docs", "Working-product demo of Sprint 1 using docs/SPRINT_PLAN.md video script (Part-2 item 2g-2h).", ["Video of about 1 minute committed under videos/ (or linked)", "Shows only features merged to main"]),
 ("CH-12", "Record and upload the Sprint-2 video (2 minutes)", 2, "Member 2", 2, "docs", "Working-product demo of the full shell (Part-2 item 3b).", ["About 2 minutes, uploaded to videos/"]),
 ("CH-13", "Complete documentation and record deviations from submitted documents", 2, "Member 4", 5, "docs", "Update SRS/SAD/STP where behaviour changed; fill docs/DEVIATIONS.md; refresh the RTM and test results (Part-2 items 2i, 3c).", ["docs/DEVIATIONS.md lists every deviation with reason", "Documents match the code at freeze"]),
 ("CH-14", "Review and integrate all PRs; final regression and release tag", 2, "Member 1", 3, "build", "Owner review of remaining PRs, run make test and make sanitize on main, tag v1.0 and freeze (Part-2 item 3d).", ["Tag v1.0 created", "No open PRs", "main protected"]),
 ("CH-15", "Integration check at the end of Sprint 1", 1, "Member 1", 1, "build", "Merge order and conflict check; verify the Sprint-1 demo builds from main.", ["main builds with 0 warnings and sprint-1 tests pass"]),
]

def comp(files):
    f = files.replace("`", "")
    for k, v in (("parser", "parser"), ("executor", "executor"), ("builtins", "builtins"), ("shell.c", "shell"), ("main.c", "shell"), ("utils", "utils")):
        if k in f: return v
    return "build"

def sev(t): return "high" if t == "High" else "medium"
items = []
FR = {f[0]: f for f in D.FR}
for fid, (sp, owner, pts, so_that) in FR_PLAN.items():
    f = FR[fid]; r = rtm[fid]
    body_ac = [f[4], "Behaviour: " + f[5], "Errors: " + f[6].replace("See FR-07 for exec failures and the fork()/pipe() failure rule below: if fork() or pipe() fails", "See FR-07 for exec failures. If fork() or pipe() fails")]
    items.append(dict(id=fid, title=f"{fid} {f[1]}", type="feature", req=fid, epic=f[2], component=comp(f[9]), priority=sev(f[3]), points=pts, sprint=sp, owner=owner,
        story=f"As a user, I want {f[1][0].lower() + f[1][1:]}, so that {so_that}.", ac=body_ac, tests=r["tests"], systests=r["systests"], files=r["files"], design=f[8], arch=f[7]))
for x in D.NFR:
    sp, owner, pts = NFR_PLAN[x[0]]; r = rtm[x[0]]
    items.append(dict(id=x[0], title=f"{x[0]} {x[1]}", type="nfr", req=x[0], epic="Non-functional", component=comp(r["files"]), priority="high", points=pts, sprint=sp, owner=owner,
        story=f"As the team, we need the product to meet {x[0]} ({x[1].lower()}) so that quality is measurable and verified.", ac=[x[2], "Verified by: " + x[3]], tests=r["tests"], systests=r["systests"], files=r["files"], design="", arch=""))
for s in D.SR:
    sp, owner, pts = SR_PLAN[s[0]]; r = rtm[s[0]]
    items.append(dict(id=s[0], title=f"{s[0]} Security: " + s[2].split(" shall ")[0][:60] if False else f"{s[0]} {SO_TXT[s[1]]} ({s[1]})", type="security", req=s[0], epic="Security", component=comp(s[6]), priority=sev(s[3]), points=pts, sprint=sp, owner=owner,
        story=f"As a security reviewer, I want {s[0]} to hold, so that objective {s[1]} ({SO_TXT[s[1]].lower()}) is met.", ac=[s[2]], tests=r["tests"], systests=r["systests"], files=s[6], design=s[5], arch=s[4]))
for (cid, title, sp, owner, pts, c, desc, ac) in CHORES:
    items.append(dict(id=cid, title=f"{cid} {title}", type="chore", req="", epic="Project setup and delivery", component=c, priority="high", points=pts, sprint=sp, owner=owner,
        story=desc, ac=ac, tests="", systests="", files="", design="", arch=""))

# validation
for it in items:
    assert it["points"] in SCALE, it["id"]
assert {i["req"] for i in items if i["type"] == "feature"} == {f[0] for f in D.FR}
assert {i["req"] for i in items if i["type"] == "nfr"} == {n[0] for n in D.NFR}
assert {i["req"] for i in items if i["type"] == "security"} == {s[0] for s in D.SR}

def body(it):
    sp = SPRINTS[it["sprint"]][0]
    b = [f"**Story**\n\n{it['story']}\n"]
    if it["req"]:
        b.append(f"**Requirement:** {it['req']} (see `docs/SRS.docx` and `docs/RTM.md`)  \n**Epic:** {it['epic']}  \n**Architecture / design refs:** {it['arch'] or '-'} / {it['design'] or '-'}  \n**Source files:** {it['files'] or '-'}\n")
    b.append("**Acceptance criteria**\n\n" + "\n".join(f"- [ ] {a}" for a in it["ac"]) + "\n")
    if it["tests"] or it["systests"]:
        b.append(f"**Tests that must pass:** {it['tests'] or '-'}" + (f"  \n**System tests:** {it['systests']}" if it["systests"] else "") + "\n")
    b.append(f"**Story points:** {it['points']}  \n**Sprint:** {sp}  \n**Owner (documented in Part-1 ownership table):** {it['owner']}  \n**Priority:** {it['priority']}\n")
    b.append("**Definition of done**\n\n- [ ] Code (or document) merged to `main` through a pull request raised by the assignee and reviewed by the repo owner\n- [ ] CI is green (build, unit, functional, system tests)\n- [ ] Linked tests pass and any new behaviour has a test\n- [ ] SRS/SAD/STP still match; any deviation is written in `docs/DEVIATIONS.md`\n- [ ] PR description contains `Closes #<this issue>`")
    return "\n".join(b)

for it in items:
    it["labels"] = [f"type:{it['type']}", f"component:{it['component']}", f"priority:{it['priority']}", f"sp:{it['points']}", f"sprint:{it['sprint']}"]
    it["milestone"] = SPRINTS[it["sprint"]][0]
    it["body"] = body(it)
order = {"chore": 0, "feature": 1, "security": 2, "nfr": 3}
items.sort(key=lambda i: (i["sprint"], order[i["type"]], i["id"]))

with open(os.path.join(ROOT, "backlog", "backlog.json"), "w") as f:
    json.dump([{k: it[k] for k in ("id", "title", "body", "labels", "milestone", "owner", "points", "sprint", "type")} for it in items], f, indent=1)
with open(os.path.join(ROOT, "backlog", "backlog.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["ID", "Title", "Type", "Requirement", "Epic", "Component", "Priority", "Story Points", "Sprint", "Owner", "Tests", "Source files"])
    for it in items: w.writerow([it["id"], it["title"], it["type"], it["req"], it["epic"], it["component"], it["priority"], it["points"], SPRINTS[it["sprint"]][0], it["owner"], it["tests"], it["files"]])

# ---- totals
tot = {(m, s): 0 for m in MEMBERS for s in SPRINTS}
for it in items: tot[(it["owner"], it["sprint"])] += it["points"]
sp_tot = {s: sum(i["points"] for i in items if i["sprint"] == s) for s in SPRINTS}
n_by = {s: sum(1 for i in items if i["sprint"] == s) for s in SPRINTS}

def table(head, rows):
    o = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    for r in rows: o.append("| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |")
    return "\n".join(o) + "\n"
def sprint_table(s):
    return table(["ID", "Story", "Type", "Points", "Owner", "Priority", "Linked tests"], [[i["id"], i["title"][len(i["id"]) + 1:], i["type"], i["points"], i["owner"], i["priority"], (i["tests"] + (", " + i["systests"] if i["systests"] and i["systests"] != "-" else "")) if i["tests"] else "-"] for i in items if i["sprint"] == s])

per_member = table(["Member"] + [SPRINTS[s][0] for s in SPRINTS] + ["Total"], [[m] + [tot[(m, s)] for s in SPRINTS] + [sum(tot[(m, s)] for s in SPRINTS)] for m in MEMBERS] + [["**Total**"] + [sp_tot[s] for s in SPRINTS] + [sum(sp_tot.values())]])
epics = {}
for i in items: epics.setdefault(i["epic"], []).append(i)
epic_tbl = table(["Epic", "Stories", "Points", "Sprint(s)"], [[e, len(v), sum(x["points"] for x in v), ", ".join(sorted({str(x["sprint"]) for x in v}))] for e, v in epics.items()])
assert all(tot[(m, s)] > 0 for m in MEMBERS for s in (1, 2)), "every member must have work in both sprints"

plan = f"""# Backlog and Sprint Plan - Simple Shell (mysh)

Prepared for **Mini-Project Deliverables Part-2** (backlog due 12 Oct 2026; Sprint 1: 19-23 Oct; Sprint 2: 26-30 Oct). Generated by `backlog/build_backlog.py` from the SRS data (`docs/docdata.py`) and the traceability matrix (`docs/RTM.md`), so story IDs, tests and files always match the submitted SRS, SAD and Test Plan.

## 1. Part-2 requirements and where they are met

| Part-2 item | Where |
|---|---|
| 1a Project linked to the repo | CH-01, CH-02; `scripts/setup_github.sh` creates and links the Project |
| 1b Backlog from the FRs and NFRs | {len([i for i in items if i['type']=='feature'])} feature stories (FR-01..FR-22), {len([i for i in items if i['type']=='nfr'])} NFR stories, {len([i for i in items if i['type']=='security'])} security stories (SR-01..SR-10) and {len([i for i in items if i['type']=='chore'])} chores = **{len(items)} backlog items** (`backlog/backlog.csv`, `backlog/backlog.json`) |
| 1c Story points | Fibonacci scale in section 2; every item has points; total {sum(sp_tot.values())} |
| 1d Assignment to members | Section 5-7 tables; the owner follows the Part-1 product-ownership table; GitHub usernames in `backlog/team.json` |
| 1e Two sprints planned | Sprint 1 (section 6) and Sprint 2 (section 7) |
| 1f Dry run 12-16 Oct | Sprint 0 (section 5) |
| 1g Changes allowed on 19 Oct | Section 9 (change control) |
| 2b GitHub Actions | `.github/workflows/` (CH-07) |
| 2c-2d PRs raised by the assignee, reviewed by the repo owner | Section 8 and `.github/PULL_REQUEST_TEMPLATE.md`, CODEOWNERS |
| 2g-2h 1-minute video | CH-11 and video script in section 6.4 |
| 2i Deviations documented | `docs/DEVIATIONS.md` |
| 3b-3d 2-minute video, documentation, freeze | CH-12, CH-13, CH-14 |

## 2. Estimation

**Story points** use the scale 1, 2, 3, 5, 8, 13 and measure *relative size* (complexity, risk and effort together), not hours:

| Points | Meaning | Example |
|---|---|---|
| 1 | Trivial, one function, nothing to decide | `pwd` built-in (FR-09) |
| 2 | Small and well understood | `>>` redirection (FR-15) |
| 3 | A few functions, some edge cases | `cd` with `-` and errors (FR-08) |
| 5 | A module part with several interacting cases | Prompt and read loop with EINTR and EOF (FR-01) |
| 8 | Largest items: many cases or tricky OS behaviour | Tokenizer with quoting (FR-03), pipelines (FR-18) |

**Capacity assumption (to be calibrated after the dry run):** about 15-22 points per member per sprint week. The first sprint's actual velocity replaces this assumption when Sprint 2 is finalised on 19 Oct.

**Backlog size:** {len(items)} items, {sum(sp_tot.values())} points.

{epic_tbl}
**Load per member and sprint (points):**

{per_member}
## 3. Team and ownership

Ownership follows the Part-1 table: Member 1 shell core and execution (FR-01, 02, 05, 06, 19, 22); Member 2 parser, built-ins, environment (FR-03, 08, 09, 12, 13); Member 3 redirection, pipes, background, signals (FR-14, 15, 16, 18, 20, 21); Member 4 error handling, exit/help, integration and verification (FR-04, 07, 10, 11, 17). Chores, non-functional and security stories are spread so that every member has work in both sprints. Real names and GitHub usernames go into `backlog/team.json` before running the setup script.

## 4. Definition of done (applies to every item)

1. Work is on a branch named `feature/<id>-short-name` (or `fix/`, `docs/`, `test/`, `chore/`).
2. The **assigned team member** raises a pull request containing `Closes #<issue>`.
3. CI is green (build with `-Werror`, unit, functional, security, pseudo-terminal tests; sanitizer job).
4. The **repo owner** reviews and merges (CODEOWNERS enforces the review request).
5. Linked tests from the issue pass; new behaviour has a test; SRS/SAD/STP still match or the difference is in `docs/DEVIATIONS.md`.

## 5. Sprint 0 - dry run (12-16 Oct)

Goal: set up GitHub (repo, Project, labels, milestones, issues, templates) and practise the PR cycle so Sprint 1 runs smoothly. Not graded as a sprint; items are small.

{sprint_table(0)}
| Day | Plan |
|---|---|
| Mon 12 Oct | Backlog creation deadline: CH-01, CH-02, CH-03 (repo, Project, issues with points and assignees) |
| Tue 13 Oct | CH-04 practice PR with owner review |
| Wed 14 Oct | CH-05 each member raises a practice PR |
| Thu 15 Oct | CH-06 practice recording; agree upload method (videos are large: Git LFS, or GitHub release asset linked from the README) |
| Fri 16 Oct | Dry-run retrospective: adjust points and assignees if needed |

## 6. Sprint 1 (19-23 Oct) - working shell core

**Sprint goal:** a working interactive shell that runs programs, understands quoting, has the built-ins (`cd`, `pwd`, `exit`, `help`), supports `<`, `>`, `>>`, `;`, reports errors correctly, and is built and tested automatically by GitHub Actions.

**Committed:** {n_by[1]} items, {sp_tot[1]} points.

{sprint_table(1)}
### 6.1 Day plan

| Day | Plan |
|---|---|
| Mon 19 Oct | Planning; CH-10 (utils) and CH-07 (Actions) first, because everything depends on them; start FR-01, FR-03 |
| Tue 20 Oct | FR-05, FR-06, FR-04 branches; first PRs reviewed |
| Wed 21 Oct | Built-ins (FR-08..FR-11), redirection (FR-14..FR-17) PRs |
| Thu 22 Oct | FR-02, FR-19, FR-22, tests (CH-08, CH-09); CH-15 integration check |
| Fri 23 Oct | Merge freeze at noon; CH-11 record the video; sprint review and retrospective |

### 6.2 Exit criteria

main builds with 0 warnings; Sprint-1 tests (listed per story) pass in CI; the demo below runs from main.

### 6.3 Sprint-1 scope note

Environment variables and `$VAR` expansion (FR-12, FR-13), pipes (FR-18), background jobs (FR-20), signals (FR-21) and the security/NFR verification stories are deliberately in Sprint 2.

### 6.4 One-minute video script (CH-11)

| Time | Show | Say |
|---|---|---|
| 0:00-0:08 | `make` then `./mysh`; prompt appears | Project and Sprint-1 goal |
| 0:08-0:20 | `pwd`, `echo Hello`, `ls`, `cd ..`, `pwd` | External commands and built-ins |
| 0:20-0:32 | `echo "a   b"` and `echo 'single quotes'` (quoting), `help` | Quoting and the built-in list |
| 0:32-0:45 | `echo one > f.txt`, `echo two >> f.txt`, `cat < f.txt` | Redirection |
| 0:45-0:55 | `invalidcommand`, `cd nosuchdir`, `echo "oops` | Error handling |
| 0:55-1:00 | `exit`; show green CI run and merged PR list | Summary |

## 7. Sprint 2 (26-30 Oct) - pipes, jobs, signals, hardening, documents

**Sprint goal:** complete the SRS: pipelines, `$VAR` expansion, background jobs, Ctrl+C handling, all non-functional and security requirements verified, documentation complete, development frozen.

**Committed:** {n_by[2]} items, {sp_tot[2]} points.

{sprint_table(2)}
### 7.1 Day plan

| Day | Plan |
|---|---|
| Mon 26 Oct | Sprint-2 planning with Sprint-1 velocity; FR-12, FR-13, FR-18 start |
| Tue 27 Oct | FR-18 pipelines, FR-20 background; security stories SR-01, SR-02, SR-07 |
| Wed 28 Oct | FR-21 signals; SR-05, SR-08, SR-10; fuzzing (SR-06); NFR verification |
| Thu 29 Oct | CH-13 documentation and deviations; CH-12 record the video; final review |
| Fri 30 Oct | CH-14: regression on main, tag `v1.0`, **freeze** (no merges after the tag) |

### 7.2 Two-minute video script (CH-12)

| Time | Show | Say |
|---|---|---|
| 0:00-0:15 | Prompt, `pwd`, `echo Hello`, `cd`, `export` / `$NAME` | Recap of Sprint 1 |
| 0:15-0:40 | `cat file | grep x`, `printf ... | sort | uniq`, `sort < in | head -1 > out` | Pipes with redirection |
| 0:40-1:00 | `sleep 5 &`, prompt returns at once, `Done` notice; `sleep 30` then Ctrl+C, `echo $?` prints 130 | Background jobs and signals |
| 1:00-1:20 | Injection demo: `X="a; echo pwned"; echo $X`; `echo "a; echo injected" > f` | Security requirements SR-01, SR-02 |
| 1:20-1:45 | `make test` summary and `make fuzz` result; CI page | Verification |
| 1:45-2:00 | RTM / DEVIATIONS.md, tag v1.0 | Documentation and freeze |

## 8. Working agreement and GitHub automation

* **Branches and PRs:** one issue = one branch = one PR. The assignee raises the PR; the repo owner reviews and merges (squash). Direct pushes to `main` are not used.
* **Commit messages:** `<id>: short imperative summary`, e.g. `FR-09: add pwd built-in`.
* **GitHub Actions** (`.github/workflows/`):
  * `ci.yml` - on every push and PR: build with `-Werror`, unit, functional/security/non-functional tests, pseudo-terminal tests, fuzzers; separate sanitizer job; test result files uploaded as an artifact and summarised on the run page.
  * `pr-hygiene.yml` - checks that the PR title starts with a backlog ID and the description links an issue (`Closes #n`), and comments if not.
  * `labeler.yml` - labels PRs by component from the files changed.
  * `project-automation.yml` (optional) - adds new issues and PRs to the Project; needs a token secret `PROJECT_TOKEN` and the Project URL variable `PROJECT_URL`.
* **Timing tests:** a few tests measure time (NF-01 to NF-03, TC-36, TC-74). Shared GitHub runners can be slow; if one fails only on CI, re-run once before raising a defect.

## 9. Change control

The backlog may be edited until 19 Oct (Part-2 item 1g). After that, scope changes are made by editing the issue (points, sprint, assignee) and noting the reason in the issue comment. Behavioural differences from the submitted SRS, SAD or Test Plan are recorded in `docs/DEVIATIONS.md` and explained in the final demo.

## 10. Risks

| Risk | Mitigation |
|---|---|
| Members are new to Git/PR flow | Sprint 0 practice PRs |
| Merge conflicts in `executor.c` (shared by Members 1, 3 and 4) | Small PRs, merge order in the day plan, CH-15 integration check |
| Video upload size | Keep under 100 MB per file (GitHub limit); use Git LFS or a release asset linked from the README |
| CI timing tests flaky on shared runners | Generous thresholds; re-run once |
| Velocity estimate wrong | Calibrate after Sprint 0/1; move items between sprints before 19 Oct without penalty |

## 11. Full backlog

{table(["ID", "Title", "Type", "Points", "Sprint", "Owner", "Labels"], [[i["id"], i["title"][len(i["id"]) + 1:], i["type"], i["points"], i["milestone"], i["owner"], ", ".join(i["labels"])] for i in items])}
"""
open(os.path.join(ROOT, "docs", "SPRINT_PLAN.md"), "w").write(plan)
print(f"{len(items)} items, {sum(sp_tot.values())} points; by sprint {sp_tot}; per member:")
for m in MEMBERS: print("  ", m, [tot[(m, s)] for s in SPRINTS])
