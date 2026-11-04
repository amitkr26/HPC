#!/bin/bash
echo "=== Q9: File Counting and Sorting ==="
printf "apple\nbanana\napple\ncherry\nbanana\napple\n" > /home/yusra/q9_file.txt
echo "wc:"
wc /home/yusra/q9_file.txt
echo "sort:"
sort /home/yusra/q9_file.txt
echo "grep apple:"
grep "apple" /home/yusra/q9_file.txt
rm -f /home/yusra/q9_file.txt
echo "Q9 done"