#!/bin/bash
echo "=== Q37: Nano: Basic Navigation ==="
echo "Creating file with multiple lines..."
for i in $(seq 1 10); do echo "Line number $i"; done > /home/yusra/q38_file.txt
echo "Navigating with arrow keys and shortcuts:"
nano /home/yusra/q38_file.txt << 'NA'
^F
^B
^A
^E
^_ (jump to line 3)
NA
echo "After nano navigation - first 3 lines:"
head -3 /home/yusra/q38_file.txt
rm -f /home/yusra/q38_file.txt
echo "Q38 done"