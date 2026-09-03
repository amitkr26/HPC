#!/bin/bash
echo "=== Q33: Vi: Deleting Text ==="
echo "Creating file with test content..."
echo "Line 1
Line 2
Line 3
Line 4
Line 5" > /home/yusra/q33_file.txt
echo "Deleting characters (x), words (dw), lines (dd), to end of line (d$), undo (u):"
vi /home/yusra/q33_file.txt << 'DEL'
x
2dw
dd
d$
u
u
:wq
DEL
echo "After vi deletions - content:"
cat /home/yusra/q33_file.txt
rm -f /home/yusra/q33_file.txt
echo "Q33 done"