#!/bin/bash
echo "=== Q4: File Linking and Deletion ==="
echo "Original content" > /home/yusra/q4_original.txt
ln /home/yusra/q4_original.txt /home/yusra/q4_hardlink
echo "Before deletion:"
ls -l /home/yusra/q4*
rm /home/yusra/q4_original.txt
echo "After deleting original:"
ls -l /home/yusra/q4_hardlink
echo "Hard link still has content:"
cat /home/yusra/q4_hardlink
rm -f /home/yusra/q4_hardlink
echo "Q4 done"