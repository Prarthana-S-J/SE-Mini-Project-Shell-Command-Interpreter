#!/usr/bin/env bash
# setup_github.sh - create labels, sprint milestones, the GitHub Project (linked to the repo) and one
# issue per backlog item (story points, sprint, assignee), then add every issue to the Project.
#
# Prerequisites:  GitHub CLI (gh), jq, `gh auth login`, and `gh auth refresh -s project`.
# Fill in backlog/team.json first (repo_owner and each member's GitHub username).
#
# Usage:   scripts/setup_github.sh <owner>/<repo>          create everything
#          DRY_RUN=1 scripts/setup_github.sh <owner>/<repo>   only print the commands (no GitHub calls)
#
# The script is idempotent for labels and milestones; run it only ONCE for issues (it would create duplicates).
set -euo pipefail

REPO="${1:?usage: $0 <owner>/<repo>}"
OWNER="${REPO%%/*}"
DRY="${DRY_RUN:-0}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
BACKLOG="$HERE/backlog/backlog.json"
TEAM="$HERE/backlog/team.json"
PROJECT_TITLE="${PROJECT_TITLE:-Simple Shell (mysh) - SE Mini Project}"

run() { if [ "$DRY" = 1 ]; then printf '+'; printf ' %q' "$@"; printf '\n'; else "$@"; fi; }
need() { command -v "$1" >/dev/null 2>&1 || { echo "missing tool: $1" >&2; exit 1; }; }
need jq
[ "$DRY" = 1 ] || need gh

owner_login() { jq -r '.repo_owner' "$TEAM"; }
gh_user() { jq -r --arg m "$1" '.members[$m].github' "$TEAM"; }
if [ "$DRY" != 1 ]; then
  for m in "Member 1" "Member 2" "Member 3" "Member 4"; do
    [ -n "$(gh_user "$m")" ] || { echo "Fill in backlog/team.json (github username for $m) first." >&2; exit 1; }
  done
  [ -n "$(owner_login)" ] || { echo "Fill in repo_owner in backlog/team.json first." >&2; exit 1; }
fi

echo "== 1. Labels"
jq -r '[.[].labels[]] | unique[]' "$BACKLOG" | while read -r label; do
  case "$label" in
    type:feature) c=1d76db;; type:nfr) c=5319e7;; type:security) c=b60205;; type:chore) c=cfd3d7;;
    priority:high) c=d93f0b;; priority:medium) c=fbca04;; sp:*) c=c5def5;; sprint:*) c=0e8a16;; *) c=ededed;;
  esac
  run gh label create "$label" --repo "$REPO" --color "$c" --force
done
run gh label create "type:bug" --repo "$REPO" --color d73a4a --force
for comp in parser executor builtins shell utils tests docs build; do
  run gh label create "component:$comp" --repo "$REPO" --color 006b75 --force
done

echo "== 2. Milestones (sprints)"
mk_ms() { run gh api -X POST "repos/$REPO/milestones" -f title="$1" -f due_on="$2T23:59:59Z" -f description="$3" || true; }
mk_ms "Sprint 0 (dry run)" 2026-10-16 "Dry run 12-16 Oct 2026: repo, Project, PR practice"
mk_ms "Sprint 1"           2026-10-23 "19-23 Oct 2026: working shell core + GitHub Actions + 1-minute video"
mk_ms "Sprint 2"           2026-10-30 "26-30 Oct 2026: pipes, jobs, signals, hardening, documentation, 2-minute video, freeze"

echo "== 3. CODEOWNERS (repo owner reviews every PR)"
if [ "$DRY" = 1 ]; then echo "+ write .github/CODEOWNERS with: * @<repo_owner>"; else
  printf '# Repo owner reviews and merges every pull request\n* @%s\n' "$(owner_login)" > "$HERE/.github/CODEOWNERS"
  echo "written .github/CODEOWNERS - commit and push it"
fi

echo "== 4. GitHub Project (v2), linked to the repo"
if [ "$DRY" = 1 ]; then
  PNUM=1; PID=PROJECT_ID
  run gh project create --owner "$OWNER" --title "$PROJECT_TITLE" --format json
else
  PJSON="$(gh project create --owner "$OWNER" --title "$PROJECT_TITLE" --format json)"
  PNUM="$(jq -r '.number' <<<"$PJSON")"; PID="$(jq -r '.id' <<<"$PJSON")"
fi
run gh project link "$PNUM" --owner "$OWNER" --repo "$REPO"
run gh project field-create "$PNUM" --owner "$OWNER" --name "Story Points" --data-type NUMBER
run gh project field-create "$PNUM" --owner "$OWNER" --name "Sprint" --data-type SINGLE_SELECT --single-select-options "Sprint 0 (dry run),Sprint 1,Sprint 2"
if [ "$DRY" = 1 ]; then SP_FIELD=SP_FIELD_ID
else SP_FIELD="$(gh project field-list "$PNUM" --owner "$OWNER" --format json | jq -r '.fields[] | select(.name=="Story Points") | .id')"; fi

echo "== 5. Issues (one per backlog item) and Project items"
COUNT="$(jq 'length' "$BACKLOG")"
for i in $(seq 0 $((COUNT - 1))); do
  id="$(jq -r ".[$i].id" "$BACKLOG")"
  title="$(jq -r ".[$i].title" "$BACKLOG")"
  body="$(jq -r ".[$i].body" "$BACKLOG")"
  labels="$(jq -r ".[$i].labels | join(\",\")" "$BACKLOG")"
  ms="$(jq -r ".[$i].milestone" "$BACKLOG")"
  pts="$(jq -r ".[$i].points" "$BACKLOG")"
  member="$(jq -r ".[$i].owner" "$BACKLOG")"
  assignee="$([ "$DRY" = 1 ] && echo "<github-user-of-$member>" || gh_user "$member")"
  if [ "$DRY" = 1 ]; then
    run gh issue create --repo "$REPO" --title "$title" --body "(body of $id)" --label "$labels" --milestone "$ms" --assignee "$assignee"
    run gh project item-add "$PNUM" --owner "$OWNER" --url "<issue-url>" --format json
    run gh project item-edit --id "<item-id>" --project-id "$PID" --field-id "$SP_FIELD" --number "$pts"
  else
    url="$(gh issue create --repo "$REPO" --title "$title" --body "$body" --label "$labels" --milestone "$ms" --assignee "$assignee")"
    item="$(gh project item-add "$PNUM" --owner "$OWNER" --url "$url" --format json | jq -r '.id')"
    gh project item-edit --id "$item" --project-id "$PID" --field-id "$SP_FIELD" --number "$pts" >/dev/null
    echo "$id -> $url"
  fi
done

echo "== 6. Optional: protect main (require 1 review and the CI check). May fail on private repos without a paid plan."
if [ "$DRY" = 1 ]; then echo "+ gh api -X PUT repos/$REPO/branches/main/protection ... (require PR review + check 'build-and-test')"; else
  gh api -X PUT "repos/$REPO/branches/main/protection" --input - <<JSON || echo "branch protection not applied (set it manually in Settings > Branches)"
{ "required_status_checks": { "strict": true, "contexts": ["build-and-test"] },
  "enforce_admins": false,
  "required_pull_request_reviews": { "required_approving_review_count": 1, "require_code_owner_reviews": true },
  "restrictions": null }
JSON
fi
echo "Done. Next: set a Sprint value on each Project item (or group the board by Milestone) and open the Project board."
