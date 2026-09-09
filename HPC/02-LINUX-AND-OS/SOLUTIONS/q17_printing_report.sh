#!/bin/bash
echo "=== Q17: Printing and Reporting ==="
echo "=== Report ===" > /home/yusra/q17_report.txt
banner "Linux Lab Report" >> /home/yusra/q17_report.txt
date >> /home/yusra/q17_report.txt
echo "---" >> /home/yusra/q17_report.txt
cal >> /home/yusra/q17_report.txt
echo "---" >> /home/yusra/q17_report.txt
bc <<< "10 + 20" >> /home/yusra/q17_report.txt
echo "Report contents:"
cat /home/yusra/q17_report.txt
echo "--- print simulation ---"
cat /home/yusra/q17_report.txt | head -10
rm -f /home/yusra/q17_report.txt
echo "Q17 done"