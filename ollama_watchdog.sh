#!/usr/bin/env bash
# Ollama watchdog: keeps the unlimited local model floor alive.
# Wedged model = /api/generate with stream:true produces no token within
# WATCH_TIMEOUT even though /api/tags answers -> kill daemon, restart, re-probe.
# Runs every 10 min via cron; logs to ollama_watchdog.log.

set -u
WATCH_TIMEOUT=60
LOG="$HOME/ollama_watchdog.log"
OLLAMA_BIN="$HOME/.local/ollama/bin/ollama"
PROBE_MODEL="qwen2.5:1.5b"
PROBE_PROMPT="Reply with exactly: WD_OK"

ts() { date "+%Y-%m-%d %H:%M:%S"; }
log() { echo "[$(ts)] $*" >> "$LOG"; }

# 1. Daemon reachable?
if ! curl -s -m 8 http://127.0.0.1:11434/api/tags -o /dev/null; then
    log "ALERT: daemon unreachable on :11434 - restarting"
    pkill -f "ollama serve" 2>/dev/null
    sleep 2
    (nohup "$OLLAMA_BIN" serve > /tmp/ollama-serve.log 2>&1 &)
    sleep 6
    if curl -s -m 8 http://127.0.0.1:11434/api/tags -o /dev/null; then
        log "RECOVERED: daemon back after restart"
    else
        log "FAIL: daemon still down after restart"
    fi
    exit 0
fi

# 2. Generation actually works? (wedged model = tags OK, tokens never come)
OUT=$(timeout "$WATCH_TIMEOUT" curl -sN http://127.0.0.1:11434/api/generate \
    -d "{\"model\":\"$PROBE_MODEL\",\"prompt\":\"$PROBE_PROMPT\",\"stream\":true}" 2>/dev/null \
    | python3 -c "
import json, sys
text = ''
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
    except Exception:
        continue
    text += d.get('response', '')
    if d.get('done'):
        print(text.strip()[:40])
        break
" )

if [ -n "$OUT" ]; then
    log "OK: generation healthy ($OUT)"
    exit 0
fi

# 3. Wedged -> restart daemon
log "ALERT: model wedged (no tokens in ${WATCH_TIMEOUT}s) - killing + restarting daemon"
pkill -f "ollama.*llama-server" 2>/dev/null
pkill -f "ollama serve" 2>/dev/null
sleep 3
( nohup "$OLLAMA_BIN" serve > /tmp/ollama-serve.log 2>&1 & )
sleep 8

# 4. Re-probe
OUT=$(timeout "$WATCH_TIMEOUT" curl -sN http://127.0.0.1:11434/api/generate \
    -d "{\"model\":\"$PROBE_MODEL\",\"prompt\":\"$PROBE_PROMPT\",\"stream\":true}" 2>/dev/null \
    | python3 -c "
import json, sys
text = ''
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
    except Exception:
        continue
    text += d.get('response', '')
    if d.get('done'):
        print(text.strip()[:40])
        break
" )

if [ -n "$OUT" ]; then
    log "RECOVERED: generation healthy after restart ($OUT)"
else
    log "FAIL: still wedged after restart - manual attention needed"
fi
