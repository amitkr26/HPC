#!/bin/bash
echo "=== Q7: Searching and Comparing Files ==="
echo "line1 apples" > /home/yusra/q7_file.txt
echo "line2 bananas" >> /home/yusra/q7_file.txt
echo "line3 apples" >> /home/yusra/q7_file.txt
echo "Find:"
find /home/yusra -name "q7_file.txt"
echo "File type:"
file /home/yusra/q7_file.txt
echo "Diff (comparing with itself):"
diff /home/yusra/q7_file.txt /home/yusra/q7_file.txt
rm -f /home/yusra/q7_file.txt
echo "Q7 done"