#!/bin/bash
echo "=== Q32: Vi: Basic Navigation ==="
echo "Creating file with large content..."
for i in $(seq 1 50); do echo "Line $i: This is a test line for navigation practice"; done > /home/yusra/q32_file.txt
echo "Navigating with h,j,k,l:"
vi /home/yusra/q32_file.txt << 'NAV'
h
j
k
l
w
b
e
0
$
gg
G
:wq
NAV
echo "After vi navigation - first 5 lines:"
head -5 /home/yusra/q32_file.txt
rm -f /home/yusra/q32_file.txt
echo "Q32 done"