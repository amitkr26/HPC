#!/bin/bash
echo "=== Q14: Data Filtering and Pattern Matching ==="
printf "user1 login 10:00\nuser2 login 11:00\nuser1 logout 12:00\nuser3 login 13:00\nuser1 login 14:00\n" > /home/yusra/q14_log.txt
echo "--- grep ---"
grep "user1" /home/yusra/q14_log.txt
echo "--- sort ---"
sort /home/yusra/q14_log.txt
echo "--- uniq -c ---"
sort /home/yusra/q14_log.txt | uniq -c
echo "--- wc ---"
wc /home/yusra/q14_log.txt
echo "--- head ---"
head -2 /home/yusra/q14_log.txt
echo "--- tail ---"
tail -1 /home/yusra/q14_log.txt
rm -f /home/yusra/q14_log.txt
echo "Q14 done"