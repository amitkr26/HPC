#!/bin/bash
echo "=== Q39: Nano: Searching and Replacing ==="
echo "Creating file with search test..."
echo "The quick brown fox" > /home/yusra/q40_file.txt
echo "Searching and replacing in nano:"
nano /home/yusra/q40_file.txt << 'SR'
^W
quick
^\
slow
Nano
SR
echo "After nano search/replace - content:"
cat /home/yusra/q40_file.txt
rm -f /home/yusra/q40_file.txt
echo "Q40 done"