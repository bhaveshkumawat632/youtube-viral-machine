#!/bin/bash
for topic in volcano blackhole samurai everest amazon; do
    echo "=========================================="
    echo "GENERATING: $topic"
    echo "=========================================="
    python3 build_master_real_world_short.py "$topic"
done
