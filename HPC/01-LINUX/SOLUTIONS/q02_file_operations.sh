#!/bin/bash
echo "=== Q2: File Operations ==="
touch /home/yusra/q2_file.txt
echo "Hello Linux" > /home/yusra/q2_file.txt
echo "Content:"
cat /home/yusra/q2_file.txt
echo "---tac---"
tac /home/yusra/q2_file.txt
echo "---head---"
head -1 /home/yusra/q2_file.txt
echo "---tail---"
tail -1 /home/yusra/q2_file.txt
rm -f /home/yusra/q2_file.txt
echo "Q2 done"