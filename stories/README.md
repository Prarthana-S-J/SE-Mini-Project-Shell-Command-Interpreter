# Story patches: build the shell step by step

`simple-shell-base/` is the **starting point**: it builds, but the shell is not implemented yet (`./mysh` only prints a banner). Everything else is already there: headers (the interfaces from the SAD), Makefile, all tests, documents, backlog and issue/PR templates.

The shell is added **one backlog story at a time**. Each file in this folder is a patch that adds exactly one story (or a small group of stories) and turns on the tests that story must pass. Apply them **in order**; after patch P13 you have the finished shell (identical to `simple-shell/`).

## How to work on one story (about 10 minutes of Git)

```
git checkout main && git pull
git checkout -b feature/FR-03-parser-core            # branch named after the story
git apply stories/P02-FR-03-FR-04-FR-19-parser-core.patch   # or write the code yourself, see below
make && make unit-test && bash tests/run_tests.sh    # tests of this story must pass, the rest show SKIP
git add -A && git commit -m "FR-03: tokenizer, quoting, syntax errors, ';'"
git push -u origin feature/FR-03-parser-core
gh pr create --base main --title "FR-03: tokenizer and quoting" --body "Closes #<issue number>"
```

Then CI runs, the repo owner reviews and merges, and the **next** patch can be applied on top of the updated `main`.

## Writing the code yourself instead of applying the patch

Each patch is a reference implementation. To write it yourself: read the story issue (acceptance criteria and linked tests), read the matching SAD section, implement it, and make the tests of the story pass. The list of tests a story must turn on is below; `tests/enabled_tests.txt` is the file that switches them on. Use `git diff` against the patch to compare with the reference.

## How the tests follow the stories

`tests/enabled_tests.txt` lists the test IDs that must pass at the current stage; every other test prints `SKIP (not implemented yet)`. Each story patch adds the IDs it makes pass, so CI is green at every stage and goes red the moment a change breaks an earlier story. The last patch replaces the list with `ALL`. To see every test as a real pass/fail check at any time: `MYSH_ENABLE_ALL=1 bash tests/run_tests.sh`.

## Patch order

| Order | Patch | Sprint | Stories and suggested author | Files changed | Tests it turns on |
|---|---|---|---|---|---|
| P01 | `P01-CH-10-utils-module.patch` | 1 | CH-10: Member 4 | src/utils.c | - |
| P02 | `P02-FR-03-FR-04-FR-19-parser-core.patch` | 1 | FR-03: Member 2, FR-04: Member 4, FR-19: Member 1 | src/parser.c | UT-01, UT-02, UT-04, UT-05, UT-06, UT-11, UT-12, UT-13, UT-18, UT-19 |
| P03 | `P03-FR-05-FR-06-FR-07-run-commands.patch` | 1 | FR-05: Member 1, FR-06: Member 1, FR-07: Member 4 | src/executor.c | - |
| P04 | `P04-FR-01-FR-22-prompt-loop.patch` | 1 | FR-01: Member 1, FR-22: Member 1 | src/shell.c, src/main.c | SC-11, ST-01, ST-02, ST-06, ST-08, TC-47, TC-51, TC-52 |
| P05 | `P05-FR-02-input-sources.patch` | 1 | FR-02: Member 1 | src/main.c | SC-05, SC-09, TC-01, TC-02, TC-03, TC-10, TC-21, TC-35, TC-37, TC-39, TC-40, TC-41, TC-46, TC-49, TC-50, TC-54, TC-55, TC-62, TC-63, TC-72, TC-76, TC-77 |
| P06 | `P06-FR-08-FR-11-builtins.patch` | 1 | FR-08: Member 2, FR-09: Member 2, FR-10: Member 4, FR-11: Member 4 | src/builtins.c, src/executor.c | ST-09, TC-04, TC-07, TC-31, TC-32, TC-33, TC-34, TC-53 |
| P07 | `P07-FR-14-FR-17-redirection.patch` | 1 | FR-14/15/16: Member 3, FR-17: Member 4 | src/parser.c, src/executor.c | SC-03, SC-07, TC-11, TC-12, TC-13, TC-14, TC-15, TC-22, TC-44, TC-70, TC-71, UT-08, UT-09, UT-14, UT-23, UT-24 |
| P08 | `P08-CH-07-github-actions.patch` | 1 | CH-07: Member 3 | .github/workflows/* | - |
| P09 | `P09-FR-12-FR-13-environment.patch` | 2 | FR-12: Member 2, FR-13: Member 2 (SR-07: Member 2, SR-01/SR-02 tests) | src/builtins.c, src/parser.c, src/executor.c | NF-08, SC-01, SC-02, ST-10, TC-05, TC-06, TC-08, TC-09, TC-16, TC-17, TC-23, TC-24, TC-25, TC-26, TC-28, TC-29, TC-30, TC-38, TC-48, TC-56, TC-60, TC-61, TC-64, TC-65, TC-66, UT-03, UT-17, UT-20, UT-21, UT-22 |
| P10 | `P10-FR-18-pipelines.patch` | 2 | FR-18: Member 3 | src/parser.c, src/executor.c | SC-08, TC-18, TC-19, TC-20, TC-27, TC-42, TC-43, TC-57, TC-58, TC-73, UT-07, UT-15 |
| P11 | `P11-FR-20-background-jobs.patch` | 2 | FR-20: Member 3 (SR-10: Member 3) | src/parser.c, src/executor.c, src/shell.c | NF-04, NF-07, ST-05, ST-07, TC-36, TC-45, TC-74, TC-75, UT-10, UT-16 |
| P12 | `P12-FR-21-signals.patch` | 2 | FR-21: Member 3 (SR-09: Member 4) | src/shell.c, src/executor.c | ST-03, ST-04, ST-11 |
| P13 | `P13-SR-08-close-on-exec.patch` | 2 | SR-08: Member 3, SR-05: Member 1 | src/main.c | SC-10 |
| P14 | `P14-NFR-SR-verification.patch` | 2 | NFR-01..09: Members 1, 2, 4; SR-06: Member 4 | tests/enabled_tests.txt | all remaining tests (enabled_tests.txt = ALL) |

Notes

* **Who raises the PR:** a patch may contain several stories (for example P02 holds FR-03, FR-04 and FR-19). One member raises the PR; the owners of the other stories review it and tick their story's acceptance criteria. If you prefer one PR per story, split the patch by hand with `git apply --include=<file>` or implement the part yourself.
* **Merge order:** the patches build on each other, so merge them in the order above. Members can work in parallel, but a patch applies cleanly only after the earlier ones are in `main`.
* **P01 (utils)** and **P08 (GitHub Actions)** are the first things to merge in Sprint 1 because everything else depends on them. P00 is this base project itself (put it on `main` first).
* **Deliberate demo of a defect fix:** P05 opens the script file with `fopen(..., "r")`; P13 changes it to close-on-exec (`"re"`), which is requirement SR-08 (defect D-3 in the Test Plan). The test SC-10 shows the difference.
* The folder `annotated-source-for-maintainers/` holds the source with stage markers (`//@if TAG`); it is only used to generate these patches and can be ignored.
* Check before you apply: `git apply --check stories/<patch>`.

## Verified

Every stage compiles with `-Wall -Wextra -Wpedantic -Werror` and passes its enabled tests; applying all patches in order reproduces the finished project exactly. This was checked automatically for all 15 stages.
