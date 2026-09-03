#!/bin/bash
echo "=== Q21: Basic Shell Commands Script ==="
echo "Output of various commands:"
echo "--- pwd ---"
pwd
echo "--- cd ---"
cd /home/yusra && pwd
echo "--- ls ---"
ls -la
echo "--- touch ---"
touch /home/yusra/q21_test.txt
echo "--- cat ---"
cat /home/yusra/q21_test.txt
echo "--- who ---"
whoami
echo "--- date ---"
date
echo "--- cal ---"
cal
echo "Q21 done"
rm -f /home/yusra/q21_test.txt