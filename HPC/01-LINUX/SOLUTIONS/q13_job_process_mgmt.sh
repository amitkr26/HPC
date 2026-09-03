#!/bin/bash
echo "=== Q13: User, Job, and Process Management ==="
echo "--- start background job ---"
sleep 3 &
echo "Background PID: $!"
echo "--- list jobs ---"
jobs
echo "--- find processes ---"
ps -e | grep -E "sleep|PID" || ps -e | head -5
echo "--- monitor users ---"
w | head -5
echo "Q13 done"