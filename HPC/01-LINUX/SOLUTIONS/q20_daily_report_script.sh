#!/bin/bash
echo "=== Q20: Automation Challenge - Daily Report Script ==="
cat > /home/yusra/daily_report.sh << 'EOF'
#!/bin/bash
echo "Daily System Report"
echo "==================="
echo "System hostname: $(hostname)"
echo "Current user: $USER"
echo "Current date: $(date)"
echo "Logged-in users: $(who | cut -d' ' -f1 | sort -u | tr '\n' ' ')"
echo "Top memory processes:"
ps -eo pid,comm,%mem --sort=-%mem | head -5
EOF
echo "Script created. Running:"
bash /home/yusra/daily_report.sh
rm -f /home/yusra/daily_report.sh
echo "Q20 done"