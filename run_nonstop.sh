#!/usr/bin/env bash
# VidRush NON-STOP engine — runs the full pipeline once and exits.
# Use a cron/systemd timer if you want continuous execution.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
export PATH="$HOME/.local/bin:$PATH"
export YVM_FREE_ONLY=1
export PYTHONUNBUFFERED=1
export VIDRUSH_ANIMATED=1

LOG="$DIR/nonstop.log"

# --- restart-safety: don't spawn duplicates ---
PIDFILE="$DIR/.nonstop.pid"
if [ -f "$PIDFILE" ]; then
  OLD=$(cat "$PIDFILE" 2>/dev/null)
  if [ -n "${OLD:-}" ] && kill -0 "$OLD" 2>/dev/null; then
    echo "[nonstop] already running as PID $OLD — exiting." | tee -a "$LOG"
    exit 0
  fi
fi
echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT

echo "[nonstop] ===== ENGINE START $(date) =====" | tee -a "$LOG"
/usr/bin/python3 vidrush_pipeline.py >> "$LOG" 2>&1
CODE=$?
echo "[nonstop] run exited code=$CODE @ $(date)" | tee -a "$LOG"
echo "[nonstop] done. Re-run manually or schedule via cron." | tee -a "$LOG"
rm -f "$PIDFILE"
