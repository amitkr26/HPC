#!/bin/bash
echo "=== Q23: Conditional Statements in Scripts ==="
cat > /home/yusra/q23_script.sh << 'SCRIPT'
#!/bin/bash
echo "Enter a number:"
read num
if [ "$num" -gt 0 ] 2>/dev/null; then
    echo "Positive"
elif [ "$num" -lt 0 ] 2>/dev/null; then
    echo "Negative"
else
    echo "Zero"
fi
SCRIPT
echo "Running script with input 5:"
echo "5" | bash /home/yusra/q23_script.sh
echo "Running script with input -3:"
echo "-3" | bash /home/yusra/q23_script.sh
echo "Running script with input 0:"
echo "0" | bash /home/yusra/q23_script.sh
rm -f /home/yusra/q23_script.sh
echo "Q23 done"