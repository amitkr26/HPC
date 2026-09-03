#!/bin/bash
echo "=== Q15: File Discovery and Metadata Analysis ==="
echo "--- locate ---"
locate -r "/home/yusra/.*\.txt" 2>/dev/null | head -5 || echo "locate not available"
echo "--- file ---"
file /home/yusra/q2_file.txt
echo "--- whatis ---"
whatis ls
echo "--- whereis ---"
whereis bash
echo "--- man specific sections ---"
man 5 passwd 2>/dev/null | head -5 || echo "man not available"
echo "Q15 done"