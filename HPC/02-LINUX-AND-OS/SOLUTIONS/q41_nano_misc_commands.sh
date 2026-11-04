#!/bin/bash
echo "=== Q40: Nano: Miscellaneous Useful Commands ==="
echo "Display cursor position (Ctrl+C), insert another file (Ctrl+R), justify text (Ctrl+J):"
echo "Creating file..."
echo "Justification test text input for nano demonstration purposes" > /home/yusra/q41_file.txt
nano /home/yusra/q41_file.txt << 'MISC'
^C
^R
^J
:w
MISC
echo "After nano misc - content:"
cat /home/yusra/q41_file.txt
rm -f /home/yusra/q41_file.txt
echo "Q41 done"