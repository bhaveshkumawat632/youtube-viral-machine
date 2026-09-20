#!/bin/bash
for topic in meteor desert quantum glacier mars; do
    echo "=========================================="
    echo "GENERATING: $topic"
    echo "=========================================="
    python3 build_master_real_world_short.py "$topic"
done
