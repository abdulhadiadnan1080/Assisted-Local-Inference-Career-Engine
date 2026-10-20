#!/usr/bin/env bash
# ALICE one-command installer.
#
#   ./install.sh               everything: Python env, frontend build, Typst, Ollama + both models
#   ./install.sh --no-models   skip the ~10 GB model download (pipeline falls back to heuristics)
#
# Or straight from GitHub, which clones first:
#   curl -fsSL https://raw.githubusercontent.com/abdulhadiadnan1080/Autonomous-Local-Career-Engine-ALCE-/main/install.sh | bash
#
# Anything this script downloads itself goes in ./.tools, so deleting the folder undoes it.
set -euo pipefail

REPO_URL="https://github.com/abdulhadiadnan1080/Autonomous-Local-Career-Engine-ALCE-.git"
HERMES="${ALICE_HERMES_MODEL:-hermes3:8b}"
GEMMA="${ALICE_GEMMA_MODEL:-gemma2:9b}"
OLLAMA_URL="http://127.0.0.1:11434"

PULL_MODELS=1
for arg in "$@"; do
  case "$arg" in
    --no-models) PULL_MODELS=0 ;;
    -h|--help) sed -n 2,10p "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

if [ -t 1 ]; then B=$'\033[1m'; G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; D=$'\033[2m'; N=$'\033[0m'; else B= G= Y= R= D= N=; fi
step() { printf '\n%s==>%s %s%s%s\n' "$G" "$N" "$B" "$*" "$N"; }
ok()   { printf '    %s✓%s %s\n' "$G" "$N" "$*"; }
warn() { printf '    %s!%s %s\n' "$Y" "$N" "$*"; }
die()  { printf '\n%sx %s%s\n' "$R" "$*" "$N" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

# ---------- 0. Run from a clone (clone first when piped from curl) ----------
HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || pwd)"
if [ ! -f "$HERE/app.py" ]; then
  have git || die "git is required to download ALICE"
  TARGET="${ALICE_DIR:-$PWD/alce}"
  step "Cloning ALICE into $TARGET"
  [ -d "$TARGET/.git" ] || git clone --depth 1 "$REPO_URL" "$TARGET"
  exec bash "$TARGET/install.sh" "$@"
fi
cd "$HERE"
ROOT="$PWD"
TOOLS="$ROOT/.tools"
mkdir -p "$TOOLS/bin"
export PATH="$TOOLS/bin:$PATH"

OS="$(uname -s)"
ARCH="$(uname -m)"
case "$OS" in Darwin|Linux) ;; *) die "ALICE supports macOS and Linux (got $OS)" ;; esac
have curl || die "curl is required"
HAVE_BREW=0; have brew && HAVE_BREW=1

printf '%sALICE installer%s  %s%s/%s · brew: %s%s\n' "$B" "$N" "$D" "$OS" "$ARCH" "$([ $HAVE_BREW = 1 ] && echo yes || echo no)" "$N"

# ---------- 1. Python >= 3.10 (python-jobspy needs it) ----------
step "Python environment"
py_ok() { "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; }
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3; do
  if have "$c" && py_ok "$c"; then PY="$(command -v "$c")"; break; fi
done
UV=""
if [ -z "$PY" ]; then
  warn "no Python >= 3.10 on PATH, fetching a private Python 3.12 with uv"
  if ! have uv; then
    curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="$TOOLS/bin" UV_NO_MODIFY_PATH=1 sh >/dev/null
  fi
  UV="$(command -v uv)"
  export UV_PYTHON_INSTALL_DIR="$TOOLS/python"
fi

if [ -x .venv/bin/python ] && ! py_ok .venv/bin/python; then
  warn "existing .venv is older than Python 3.10, rebuilding it"
  rm -rf .venv
fi
if [ ! -x .venv/bin/python ]; then
  if [ -n "$UV" ]; then "$UV" venv --quiet --python 3.12 .venv; else "$PY" -m venv .venv; fi
fi
if [ -n "$UV" ]; then
  "$UV" pip install --quiet --python .venv/bin/python -r requirements.txt
else
  .venv/bin/python -m pip install --quiet --upgrade pip
  .venv/bin/python -m pip install --quiet -r requirements.txt
fi
ok "$(.venv/bin/python --version) in .venv with requirements.txt installed"

# ---------- 2. Node >= 18 and the frontend build ----------
step "Frontend"
node_ok() { have node && [ "$(node -p 'process.versions.node.split(".")[0]')" -ge 18 ] 2>/dev/null; }
if ! node_ok; then
  if [ $HAVE_BREW = 1 ]; then
    brew install node >/dev/null
  else
    warn "no Node >= 18, downloading Node 22 LTS into .tools"
    case "$ARCH" in arm64|aarch64) NARCH=arm64 ;; x86_64) NARCH=x64 ;; *) die "unsupported CPU $ARCH" ;; esac
    NOS="$(echo "$OS" | tr '[:upper:]' '[:lower:]')"
    NFILE="$(curl -fsSL https://nodejs.org/dist/latest-v22.x/SHASUMS256.txt | awk '{print $2}' | grep "^node-v.*-$NOS-$NARCH.tar.gz$" | head -1)"
    [ -n "$NFILE" ] || die "could not find a Node build for $NOS-$NARCH"
    rm -rf "$TOOLS/node" && mkdir -p "$TOOLS/node"
    curl -fsSL "https://nodejs.org/dist/latest-v22.x/$NFILE" | tar -xz -C "$TOOLS/node" --strip-components 1
    for b in node npm npx; do ln -sf "$TOOLS/node/bin/$b" "$TOOLS/bin/$b"; done
  fi
fi
node_ok || die "Node >= 18 is required for the frontend"
(cd frontend && npm ci --no-audit --no-fund --silent && npm run build --silent >/dev/null)
ok "Node $(node --version), React app built into frontend/dist"

# ---------- 3. Typst (renders the tailored CV to PDF) ----------
step "Typst"
if ! have typst; then
  if [ $HAVE_BREW = 1 ]; then
    brew install typst >/dev/null
  else
    case "$OS-$ARCH" in
      Darwin-arm64) T=aarch64-apple-darwin ;;
      Darwin-x86_64) T=x86_64-apple-darwin ;;
      Linux-x86_64) T=x86_64-unknown-linux-musl ;;
      Linux-aarch64|Linux-arm64) T=aarch64-unknown-linux-musl ;;
      *) T="" ;;
    esac
    if [ -n "$T" ]; then
      TMP="$(mktemp -d)"
      if curl -fsSL "https://github.com/typst/typst/releases/latest/download/typst-$T.tar.xz" | tar -xJ -C "$TMP"; then
        mv "$TMP/typst-$T/typst" "$TOOLS/bin/typst"
      fi
      rm -rf "$TMP"
    fi
  fi
fi
if have typst; then ok "$(typst --version)"; else warn "Typst missing: CVs are saved as JSON, not PDF"; fi

# ---------- 4. Ollama and the two local models ----------
step "Ollama (local models)"
if ! have ollama; then
  if [ $HAVE_BREW = 1 ]; then
    brew install ollama >/dev/null
  elif [ "$OS" = Linux ]; then
    curl -fsSL https://ollama.com/install.sh | sh
  else
    TMP="$(mktemp -d)"
    if curl -fsSL https://github.com/ollama/ollama/releases/latest/download/ollama-darwin.tgz | tar -xz -C "$TMP"; then
      rm -rf "$TOOLS/ollama" && mv "$TMP" "$TOOLS/ollama"
      ln -sf "$TOOLS/ollama/ollama" "$TOOLS/bin/ollama"
    else
      rm -rf "$TMP"
    fi
  fi
fi
if ! have ollama; then
  warn "Ollama could not be installed. Get it from https://ollama.com/download"
  warn "ALICE still runs: every model step falls back to deterministic heuristics"
elif [ $PULL_MODELS = 0 ]; then
  ok "Ollama $(ollama --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | tail -1)"
  warn "skipped model download (--no-models). Later: ollama pull $HERMES && ollama pull $GEMMA"
else
  STARTED=""
  if ! curl -fs "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
    mkdir -p data/logs
    ollama serve >data/logs/ollama.log 2>&1 &
    STARTED=$!
    for _ in $(seq 1 30); do curl -fs "$OLLAMA_URL/api/tags" >/dev/null 2>&1 && break; sleep 0.5; done
  fi
  for m in "$HERMES" "$GEMMA"; do
    if ollama list 2>/dev/null | awk '{print $1}' | grep -qx "$m"; then
      ok "$m already pulled"
    else
      printf '    pulling %s (about 5 GB)\n' "$m"
      ollama pull "$m"
      ok "$m pulled"
    fi
  done
  [ -n "$STARTED" ] && kill "$STARTED" 2>/dev/null || true
fi

# ---------- 5. Local config (never committed) ----------
step "Config"
if [ ! -f config/master_profile.yaml ]; then
  cp config/master_profile.example.yaml config/master_profile.yaml
  ok "created config/master_profile.yaml from the example, so put your real facts in it"
else
  ok "config/master_profile.yaml already exists"
fi
[ -f .env ] || { cp .env.example .env && ok "created .env (Gmail is optional)"; }

printf '\n%s%sALICE is installed.%s\n\n' "$G" "$B" "$N"
printf '  %s./run.sh%s              start everything and open the dashboard\n' "$B" "$N"
printf '  %s./run.sh --pipeline%s   start and run the full crawl → score → tailor pipeline\n' "$B" "$N"
printf '  %s./run.sh --demo%s       start with a sample deck, no crawling\n\n' "$B" "$N"
