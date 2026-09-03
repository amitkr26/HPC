#!/bin/bash
echo "=== Q29: Countdown Timer ==="
cat > /home/yusra/q29_script.sh << 'SCRIPT'
#!/bin/bash
echo "Enter countdown seconds:"
read seconds
while [ $seconds -gt 0 ]; do
    echo "Time left: $seconds seconds"
    sleep 1
    seconds=$((seconds - 1))
done
echo "Time's up!"
SCRIPT
echo "Running with 5 seconds:"
echo "5" | bash /home/yusra/q29_script.sh
rm -f /home/yusra/q29_script.sh
echo "Q29 done"