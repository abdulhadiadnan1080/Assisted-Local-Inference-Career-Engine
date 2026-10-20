#!/usr/bin/env bash
# ALICE one-command run. Starts Ollama (if needed) and the engine, then opens the dashboard.
#
#   ./run.sh              start and open http://127.0.0.1:8471
#   ./run.sh --pipeline   also turn live crawl on and run the whole pipeline end to end
#   ./run.sh --demo       also load the 15-card sample deck (no crawling)
#   ./run.sh --no-open    do not open a browser
#
# Ctrl-C stops everything this script started.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
ROOT="$PWD"
PORT="${ALICE_PORT:-8471}"
URL="http://127.0.0.1:$PORT"
OLLAMA_URL="http://127.0.0.1:11434"
export PATH="$ROOT/.tools/bin:$PATH"

MODE=""
OPEN=1
for arg in "$@"; do
  case "$arg" in
    --pipeline) MODE=pipeline ;;
    --demo) MODE=demo ;;
    --no-open) OPEN=0 ;;
    -h|--help) sed -n 2,9p "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

if [ -t 1 ]; then B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; D=$'\033[2m'; N=$'\033[0m'; else B= G= Y= R= D= N=; fi
ok()   { printf '%s✓%s %s\n' "$G" "$N" "$*"; }
warn() { printf '%s!%s %s\n' "$Y" "$N" "$*"; }
die()  { printf '%sx %s%s\n' "$R" "$*" "$N" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }
up()   { curl -fs "$1" >/dev/null 2>&1; }

[ -x .venv/bin/python ] || die "not installed yet, run ./install.sh first"
up "$URL/health" && die "something is already running on $URL (another ALICE?)"
mkdir -p data/logs

PIDS=""
cleanup() {
  trap - EXIT
  [ -n "$PIDS" ] && kill $PIDS 2>/dev/null || true
  wait 2>/dev/null || true
  printf '\n%sALICE stopped.%s\n' "$D" "$N"
}
trap cleanup EXIT
trap 'exit 130' INT TERM

# Rebuild the React app when its sources are newer than the last build.
if [ ! -f frontend/dist/index.html ] || [ -n "$(find frontend/src frontend/index.html -newer frontend/dist/index.html -print -quit)" ]; then
  have npm || die "npm missing, run ./install.sh"
  printf 'building frontend…\n'
  (cd frontend && npm run build --silent >/dev/null)
fi

if up "$OLLAMA_URL/api/tags"; then
  ok "Ollama already running"
elif have ollama; then
  ollama serve >data/logs/ollama.log 2>&1 &
  PIDS="$PIDS $!"
  for _ in $(seq 1 30); do up "$OLLAMA_URL/api/tags" && break; sleep 0.5; done
  if up "$OLLAMA_URL/api/tags"; then ok "Ollama started"; else warn "Ollama did not start (see data/logs/ollama.log), using heuristic fallbacks"; fi
else
  warn "Ollama not installed, using heuristic fallbacks"
fi

ALICE_PORT="$PORT" .venv/bin/python app.py >data/logs/alice.log 2>&1 &
APP=$!
PIDS="$PIDS $APP"
for _ in $(seq 1 60); do
  up "$URL/health" && break
  kill -0 "$APP" 2>/dev/null || { tail -20 data/logs/alice.log >&2; die "engine failed to start"; }
  sleep 0.5
done
up "$URL/health" || die "engine did not answer on $URL"
ok "engine on $URL  ${D}(logs: data/logs/alice.log)${N}"

PAGE="/"
case "$MODE" in
  pipeline)
    curl -fs -X POST "$URL/api/settings/live-crawl" -H 'Content-Type: application/json' -d '{"enabled":true}' >/dev/null
    curl -fs -X POST "$URL/api/pipeline/run" >/dev/null || die "pipeline did not start"
    ok "pipeline started: crawl → gates → score → tailor → draft → daily 15"
    PAGE="/automate"
    ;;
  demo)
    # Every sample card goes through the real models, so this can take a while. Serve meanwhile.
    ( curl -fs -X POST "$URL/api/demo/seed" >/dev/null && ok "sample deck loaded, refresh the briefing" \
      || warn "could not load the sample deck (see data/logs/alice.log)" ) &
    PIDS="$PIDS $!"
    ok "loading the 15-card sample deck through the local models in the background"
    PAGE="/app/briefing"
    ;;
esac

if [ $OPEN = 1 ]; then
  if have open; then open "$URL$PAGE"; elif have xdg-open; then xdg-open "$URL$PAGE" >/dev/null 2>&1 || true; fi
fi
printf '\n  %sALICE is running →%s %s%s\n  %sCtrl-C to stop%s\n\n' "$B" "$N" "$URL" "$PAGE" "$D" "$N"

if [ "$MODE" = pipeline ]; then
  # Report progress until the worker finishes, then keep serving the dashboard.
  status() { curl -fs "$URL/api/pipeline/status" 2>/dev/null || echo '{}'; }
  summary() {
    .venv/bin/python -c 'import json,sys; s=json.load(sys.stdin); c=s.get("counts",{}); print("running=%d ready=%d backlog=%d review=%d archived=%d" % (bool(s.get("running")), c.get("READY",0), c.get("BACKLOG",0), c.get("NEEDS_REVIEW",0), c.get("ARCHIVED",0)))'
  }
  sleep 2
  while kill -0 "$APP" 2>/dev/null; do
    line="$(status | summary)"
    printf '\r%s%s%s   ' "$D" "${line#running=? }" "$N"
    case "$line" in running=0*) break ;; esac
    sleep 5
  done
  printf '\n'
  ok "pipeline finished. Today's picks are in $URL/app/briefing"
fi

wait "$APP"
