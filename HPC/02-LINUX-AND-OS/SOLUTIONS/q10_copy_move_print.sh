#!/bin/bash
echo "=== Q10: File Copy, Move, and Print ==="
echo "Source content" > /home/yusra/q10_source.txt
echo "Copy:"
cp /home/yusra/q10_source.txt /home/yusra/q10_copy.txt
echo "Move (rename):"
mv /home/yusra/q10_copy.txt /home/yusra/q10_renamed.txt
ls /home/yusra/q10_*
echo "ls -l:"
ls -l /home/yusra/ | grep q10
echo "Print simulation (cat to simulate lpr):"
cat /home/yusra/q10_renamed.txt
rm -f /home/yusra/q10_source.txt /home/yusra/q10_renamed.txt
echo "Q10 done"