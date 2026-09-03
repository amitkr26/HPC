#!/bin/bash
echo "=== Q27: Even or Odd Checker ==="
cat > /home/yusra/q27_script.sh << 'SCRIPT'
#!/bin/bash
echo "Enter a number:"
read num
if [ $((num % 2)) -eq 0 ]; then
    echo "$num is even"
else
    echo "$num is odd"
fi
SCRIPT
echo "Running with input 42:"
echo "42" | bash /home/yusra/q27_script.sh
echo "Running with input 27:"
echo "27" | bash /home/yusra/q27_script.sh
rm -f /home/yusra/q27_script.sh
echo "Q27 done"