# Backlog

* `backlog.csv` - spreadsheet view of all items (ID, type, requirement, story points, sprint, owner, tests, files)
* `backlog.json` - the same items with full issue bodies, used by `scripts/setup_github.sh`
* `team.json` - **fill in** `repo_owner` and each member's GitHub username before running the setup script
* `build_backlog.py` - regenerates the files above and `docs/SPRINT_PLAN.md` from the SRS data. Change story points, sprint or owner at the top of this file, re-run `python3 backlog/build_backlog.py`, and the plan, CSV and issues stay consistent.

## Creating the GitHub backlog (about 10 minutes)

1. Create an empty repository on GitHub and push this folder to it (`git init`, `git add .`, `git commit`, `git remote add origin ...`, `git push -u origin main`).
2. Install the GitHub CLI and `jq`; run `gh auth login` and `gh auth refresh -s project`.
3. Fill in `backlog/team.json`.
4. Preview: `DRY_RUN=1 scripts/setup_github.sh <owner>/<repo>` (prints the commands only).
5. Create everything: `scripts/setup_github.sh <owner>/<repo>` (labels, 3 sprint milestones, Project linked to the repo, 56 issues with story points and assignees). Run it once.
6. Commit the generated `.github/CODEOWNERS`.

Manual alternative: create the Project in the GitHub web UI, link it to the repo, and create issues from `backlog.csv` by hand or with the web "Add item" button.
