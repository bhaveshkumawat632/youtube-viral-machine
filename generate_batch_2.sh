#!/bin/bash
for topic in alien robot hacker viking tornado; do
    echo "=========================================="
    echo "GENERATING: $topic"
    echo "=========================================="
    python3 build_master_real_world_short.py "$topic"
done
