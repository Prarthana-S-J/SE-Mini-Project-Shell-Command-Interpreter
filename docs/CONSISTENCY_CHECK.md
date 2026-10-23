# Consistency Check (item 15)

Generated automatically by `docs/build_docs.py` on each run.

| Check | Result | Detail |
|---|---|---|
| Every FR has at least one PASSED executed test | PASS |  |
| Every FR has a system test (ST-10 covers all) | PASS |  |
| Every test references an existing requirement | PASS |  |
| No test failed | PASS |  |
| Every implemented built-in is documented in the SRS | PASS |  |
| Built-ins documented (cd,pwd,exit,help,export,unset,env) all exist in source | PASS | ['cd', 'pwd', 'exit', 'help', 'export', 'unset', 'env'] |
| Every function named in the design index exists in the named source file | PASS |  |
| Every code file in the RTM exists | PASS |  |
| Team table and FR owners agree; each FR has exactly one owner | PASS |  |
| Every member owns at least 5 functional requirements | PASS |  |
| All 8 diagrams exist | PASS |  |
| Source never calls system()/popen() (NFR-06) | PASS |  |
| Every security requirement has a passing test | PASS |  |
| Every security requirement serves a stated security objective | PASS |  |
| Every security objective is covered by at least 1 requirement | PASS |  |
| At least 2 security objectives and 2 security requirements (Part-1 rule) | PASS |  |
| Every NFR has at least one executed test or an inspection/build check | PASS |  |
| Every test ID mentioned in SRS/STP/SAD/RTM exists in the result files | PASS |  |
| STP has the 15 template sections and 5.1 | PASS |  |
| SAD has template sections 3.1-3.9 and 4.1-4.6 | PASS |  |
| SAD has at least 2 UML sequence diagrams | PASS |  |
| SRS has a UML use-case diagram and Security section with objectives and requirements | PASS |  |
| Part-1 minimum: at least 10 test cases covering FR, NFR and security | PASS |  |
| No template placeholder text remains | PASS |  |
| Features documented in README exist: -c, script, stdin modes tested | PASS |  |

## Checks that need a human

* Whether the ownership table reflects who really did the work.
* Whether the diagrams still match the code after future changes (re-run `python3 docs/diagrams/make_diagrams.py` and re-read `docs/DESIGN.md`).
* Whether the official Project Guidelines impose extra format rules (the uploaded Project_Guidelines.docx contained the project brief, not separate official rules).
