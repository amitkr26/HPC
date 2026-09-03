#!/bin/bash
echo "=== Q55: Demand Paging Simulation ==="
echo "Reference string: 1 2 3 4 1 2 5 1 2 3 4 5"
echo "--- FIFO Page Replacement ---"
# FIFO simulation
frame_count=3
pages="1 2 3 4 1 2 5 1 2 3 4 5"
fifo_queue=()
fifo_faults=0
for page in $pages; do
    in_queue=false
    for f in "${fifo_queue[@]}"; do
        if [ "$f" = "$page" ]; then
            in_queue=true
            break
        fi
    done
    if [ "$in_queue" = false ]; then
        fifo_faults=$((fifo_faults + 1))
        if [ ${#fifo_queue[@]} -ge $frame_count ]; then
            fifo_queue=("${fifo_queue[@]:1}")
        fi
        fifo_queue+=("$page")
    fi
done
echo "FIFO page faults: $fifo_faults (expected: 9 with 3 frames)"

echo "--- LRU Page Replacement ---"
# LRU simulation
frames=3
lru_faults=0
lru usage_order=()
for page in $pages; do
    found=false
    for i in "${!lru usage_order[@]}"; do
        if [ "${lru usage_order[$i]}" = "$page" ]; then
            found=true
            # Move to front (most recently used)
            unset 'lru usage_order[$i]'
            lru usage_order=("$page" "${lru usage_order[@]}")
            break
        fi
    done
    if [ "$found" = false ]; then
        lru_faults=$((lru_faults + 1))
        if [ ${#lru usage_order[@]} -ge $frames ]; then
            # Remove least recently used (last element)
            unset 'lru usage_order[-1]'
            lru usage_order=("$page" "${lru usage_order[@]}")
        else
            lru usage_order=("$page" "${lru usage_order[@]}")
        fi
    fi
done
echo "LRU page faults: $lru_faults (expected: 10 with 3 frames)"
rm -f /tmp/q55_*.txt
echo "Q55 done"