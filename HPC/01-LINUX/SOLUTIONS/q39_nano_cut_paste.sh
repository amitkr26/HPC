#!/bin/bash
echo "=== Q38: Nano: Cutting, Copying, and Pasting ==="
echo "Creating file with text to cut and paste..."
echo "To be or not to be
That is the question
Whether 'tis nobler" > /home/yusra/q39_file.txt
echo "Cutting (Ctrl+K), pasting (Ctrl+U), selecting (Alt+A):"
nano /home/yusra/q39_file.txt << 'CP'
^K
^U
^A
^K
^U
:w
CP
echo "After nano cut/paste - content:"
cat /home/yusra/q39_file.txt
rm -f /home/yusra/q39_file.txt
echo "Q39 done"