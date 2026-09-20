#!/bin/bash
# Autonomous render loop with explicit upload approval gates.

set -u

cd /home/junglee01/youtube-viral-machine || exit 1

if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    . ./.env
    set +a
fi

if [ "${VIDRUSH_LOOP_APPROVED:-0}" != "1" ]; then
    echo "VIDRUSH_LOOP_APPROVED is not 1. Loop disabled until the new engine is approved."
    exit 0
fi

while true; do
    echo "======================================"
    echo "Starting reference-based generation at $(date)"
    echo "======================================"

    python3 build_math_masterpiece.py

    if [ "${VIDRUSH_AUTO_UPLOAD_APPROVED:-0}" != "1" ]; then
        echo "VIDRUSH_AUTO_UPLOAD_APPROVED is not 1. Render kept local; upload skipped."
        echo "Sleeping for 4 hours..."
        sleep 14400
        continue
    fi

    cp /home/junglee01/youtube-viral-machine/output/vidrush/math_masterpiece/FINAL_VIRAL_SHORT.mp4 /home/junglee01/bhaveshkumawat632.github.io/assets/videos/PERFECT_VIRAL_SHORT.mp4

    cd /home/junglee01/bhaveshkumawat632.github.io || exit 1
    git add assets/videos/PERFECT_VIRAL_SHORT.mp4
    git commit -m "Auto-deploy approved reference-based video at $(date)"
    git push
    echo "Successfully deployed to dashboard."

    cd /home/junglee01/youtube-viral-machine || exit 1
    echo "Initiating approved YouTube upload..."
    python3 auto_upload.py

    echo "Initiating approved Instagram upload..."
    python3 ig_uploader.py

    echo "Cycle complete. Sleeping for 4 hours..."
    sleep 14400
done
