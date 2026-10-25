#!/usr/bin/env bash
# Publish one run's leaderboard into README.md and leaderboard/ on main.
#   publish_board.sh <leaderboard.json> <standard|mft> <preset> [--only-if-current]
# Builds on the newest main every attempt, so two presets finishing together both land: a rejected push simply
# re-renders on top of the other run's commit and tries again. --only-if-current: a second publish of the same run
# (with a late platform added), which never replaces a newer run of the preset.
set -euo pipefail

PAYLOAD="$(realpath "$1")"
KIND="$2"
PRESET="$3"
EXTRA=("${@:4}")
RUN_URL="${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}"

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

for attempt in 1 2 3 4 5; do
  git fetch --quiet origin main
  git checkout --quiet -B board-publish origin/main
  python ./scripts/readme_board.py \
    --ingest "$PAYLOAD" \
    --kind "$KIND" \
    --preset "$PRESET" \
    --run-id "$GITHUB_RUN_ID" \
    --run-url "$RUN_URL" \
    --sha "$GITHUB_SHA" \
    --repo "$GITHUB_REPOSITORY" \
    "${EXTRA[@]}"
  git add README.md leaderboard
  if git diff --cached --quiet; then
    echo "[publish] nothing changed"
    exit 0
  fi
  git commit --quiet -m "chore(board): ${KIND} ${PRESET} leaderboard from run ${GITHUB_RUN_ID}"
  if git push --quiet origin HEAD:main; then
    echo "[publish] README leaderboard updated: ${KIND} ${PRESET}"
    exit 0
  fi
  echo "[publish] push rejected (attempt ${attempt}); rebuilding on the new main"
  sleep $((attempt * 5))
done
echo "::warning::the ${KIND} ${PRESET} leaderboard could not be published after 5 attempts"
