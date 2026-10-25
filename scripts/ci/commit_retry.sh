#!/usr/bin/env bash
# Run a generator on the newest main and push what it changed, retrying when another job pushed first.
#   commit_retry.sh "<commit message>" "<paths to add>" <command...>
# Every attempt starts again from origin/main, so the generator always renders on top of the latest data.
set -euo pipefail

MESSAGE="$1"
PATHS="$2"
shift 2

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

for attempt in 1 2 3 4 5; do
  git fetch --quiet origin main
  git checkout --quiet -B commit-retry origin/main
  "$@"
  # shellcheck disable=SC2086  # PATHS is a fixed, space-separated list from the workflow
  git add $PATHS
  if git diff --cached --quiet; then
    echo "[commit_retry] nothing changed"
    exit 0
  fi
  git commit --quiet -m "$MESSAGE"
  if git push --quiet origin HEAD:main; then
    echo "[commit_retry] pushed: $MESSAGE"
    exit 0
  fi
  echo "[commit_retry] push rejected (attempt ${attempt}); retrying on the new main"
  sleep $((attempt * 5))
done
echo "::error::could not push after 5 attempts: $MESSAGE"
exit 1
