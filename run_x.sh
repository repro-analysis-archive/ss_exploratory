#!/usr/bin/env bash
# Exploratory analyses X1 / X2 (EXPLORATORY_PLAN_X1_X2.md, commit b6d1cf7; OSF https://osf.io/5c627): unattended
# runner, orchestration only. Imports the locked ss_benchmark unchanged from a git-archive snapshot of the main
# repository's step-7 record commit; new code lives in this repository. Logic: xplore/x_orchestrate.py.
#
#   launch / resume (detached; survives closing the terminal):
#     setsid nohup ./run_x.sh --expect-commit <SHA of this repository> > /dev/null 2>&1 < /dev/null &
#   progress counts and resource readings only:   ./run_x.sh --status
#   stop on request (resumable):                   ./run_x.sh --stop
#
# Refuses (exit 3, nothing changed) unless this repository's HEAD == --expect-commit with a clean tree, the main
# repository holds the step-7 record commit, ss_benchmark there is the SDR commit, and (real run) the step-5 files and
# the step-6 shards match their committed records. Options: --out DIR, --workers N (18), --cpus LIST,
# --main-commit SHA; PLACEHOLDER smoke tests only: --placeholder --step6-out DIR --cells LIST --max-reps M --n-boot B.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=/home/user/miniconda3/bin/python3
OUT=/media/user/LaCie/medvideo_gate/ss_exploratory_X
WORKERS=18
EXPECT=""
MODE=run
EXTRA=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --expect-commit) EXPECT="$2"; shift 2 ;;
    --status) MODE=status; shift ;;
    --stop) MODE=stop; shift ;;
    --out) OUT="$2"; shift 2 ;;
    --workers) WORKERS="$2"; shift 2 ;;
    --cpus) EXTRA+=(--cpus "$2"); shift 2 ;;
    --main-commit) EXTRA+=(--main-commit "$2"); shift 2 ;;
    --placeholder) EXTRA+=(--placeholder); shift ;;
    --step6-out) EXTRA+=(--step6-out "$2"); shift 2 ;;
    --cells) EXTRA+=(--cells "$2"); shift 2 ;;
    --max-reps) EXTRA+=(--max-reps "$2"); shift 2 ;;
    --n-boot) EXTRA+=(--n-boot "$2"); shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 64 ;;
  esac
done
export PYTHONPATH="$REPO" PYTHONDONTWRITEBYTECODE=1

if [[ $MODE == status ]]; then
  exec "$PY" -m xplore.x_orchestrate status --out "$OUT"
fi
if [[ $MODE == stop ]]; then
  PID="$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1])).get("pid", ""))' "$OUT/state.json" 2>/dev/null || true)"
  if [[ -n $PID ]] && grep -q x_orchestrate "/proc/$PID/cmdline" 2>/dev/null; then
    kill -TERM "$PID"; echo "stop requested (pid $PID); resumable with the same launch command"
  else
    echo "no running X runner for $OUT"
  fi
  exit 0
fi

refuse() { echo "$(date -Is) refused: $*" >&2; exit 3; }
[[ -n $EXPECT ]] || refuse "--expect-commit is required"
export GIT_OPTIONAL_LOCKS=0
EXP="$(git -C "$REPO" rev-parse --verify --quiet "${EXPECT}^{commit}")" || refuse "unknown commit $EXPECT"
[[ "$(git -C "$REPO" rev-parse --verify --quiet HEAD:run_x.sh)" == "$(git -C "$REPO" hash-object "${BASH_SOURCE[0]}")" ]] \
  || refuse "this script is not the one in HEAD"

mkdir -p "$OUT/logs"
exec 9>"$OUT/runner.lock"
flock -n 9 || refuse "another X runner holds $OUT/runner.lock"
cd "$REPO"
exec "$PY" -m xplore.x_orchestrate run --repo "$REPO" --expect-commit "$EXP" --out "$OUT" --workers "$WORKERS" \
  "${EXTRA[@]}" >> "$OUT/logs/runner_stdout.log" 2>&1
