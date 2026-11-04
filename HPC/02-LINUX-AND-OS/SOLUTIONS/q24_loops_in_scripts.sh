#!/bin/bash
echo "=== Q24: Loops in Shell Scripts ==="
cat > /home/yusra/q24_script.sh << 'SCRIPT'
#!/bin/bash
echo "For loop:"
for i in 1 2 3; do
    echo "  Iteration $i"
done
echo "While loop:"
count=1
while [ $count -le 3 ]; do
    echo "  Count $count"
    count=$((count + 1))
done
echo "Until loop:"
count=1
until [ $count -gt 3 ]; do
    echo "  Count $count"
    count=$((count + 1))
done
SCRIPT
echo "Running script:"
bash /home/yusra/q24_script.sh
rm -f /home/yusra/q24_script.sh
echo "Q24 done"