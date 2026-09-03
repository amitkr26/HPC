#!/bin/bash
echo "=== Q31: Vi: Opening, Inserting, Saving, and Quitting ==="
echo "Testing text to insert" > /home/yusra/q31_file.txt
echo "Now opening with vi..."
vi /home/yusra/q31_file.txt << 'INS'
i
Text inserted in insert mode
Esc
:wq
INS
echo "After vi - content:"
cat /home/yusra/q31_file.txt
rm -f /home/yusra/q31_file.txt
echo "Q31 done"