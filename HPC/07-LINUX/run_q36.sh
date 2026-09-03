#!/bin/bash
echo "=== Q35: Vi: Advanced Commands ==="
echo "Enabling line numbers and jumping:"
echo "Jump line practice" > /home/yusra/q36_file.txt
vi /home/yusra/q36_file.txt << 'AN'
:set nu
5j
0
G
:%s/Jump/Leap/g
:wq
AN
echo "After vi advanced - content with line numbers:"
cat /home/yusra/q36_file.txt
rm -f /home/yusra/q36_file.txt
echo "Q36 done"