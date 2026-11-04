#!/bin/bash
echo "=== Q33: Vi: Copying and Pasting ==="
echo "Creating file with text to copy..."
echo "To be or not to be
That is the question" > /home/yusra/q34_file.txt
echo "Yanking (yy) and putting (p):"
vi /home/yusra/q34_file.txt << 'YP'
yy
p
 yy
P
:wq
YP
echo "After vi yank/paste - content:"
cat /home/yusra/q34_file.txt
rm -f /home/yusra/q34_file.txt
echo "Q34 done"