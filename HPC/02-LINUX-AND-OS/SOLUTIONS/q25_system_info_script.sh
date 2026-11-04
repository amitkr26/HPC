#!/bin/bash
echo "=== Q25: Script to Display System Info ==="
cat > /home/yusra/q25_script.sh << 'SCRIPT'
#!/bin/bash
echo "System Information Report"
echo "========================="
echo "Date: $(date)"
echo "User: $USER"
echo "Logged-in users: $(who | cut -d' ' -f1 | sort -u | tr '\n' ' ')"
echo "Top memory processes:"
ps -eo pid,comm,%mem --sort=-%mem | head -5
echo "Disk usage:"
df -h /home
SCRIPT
echo "Running system info script:"
bash /home/yusra/q25_script.sh
rm -f /home/yusra/q25_script.sh
echo "Q25 done"