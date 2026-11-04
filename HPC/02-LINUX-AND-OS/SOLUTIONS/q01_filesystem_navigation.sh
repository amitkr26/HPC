#!/bin/bash
echo "=== Q1: Navigating Linux Filesystem ==="
mkdir -p /home/yusra/q1_test/a/b/c
echo "Step 1: Created nested dirs"
pwd
cd /home/yusra/q1_test/a/b/c
echo "Step 2: Changed to nested dir"
pwd
cd ../../..
echo "Step 3: Went back to root of test"
pwd
rm -rf /home/yusra/q1_test
echo "Step 4: Cleaned up"
ls /home/yusra/ | grep q1