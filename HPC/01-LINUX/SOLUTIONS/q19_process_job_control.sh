#!/bin/bash
echo "=== Q19: Process State and Job Control ==="
echo "--- run background job ---"
sleep 2 &
JOB_PID=$!
echo "Job PID: $JOB_PID"
echo "--- check job IDs ---"
jobs
echo "--- terminate with kill ---"
kill $JOB_PID
echo "Job terminated"
echo "--- verify ---"
jobs
echo "Q19 done"