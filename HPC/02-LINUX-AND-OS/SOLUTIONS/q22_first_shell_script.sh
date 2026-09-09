#!/bin/bash
echo "=== Q22: Writing Your First Shell Script ==="
chmod +x /home/yusra/first_script.sh
cat > /home/yusra/first_script.sh << 'SCRIPT'
#!/bin/bash
echo "Hello from shell script!"
echo "Current date:"
date
echo "Current user: $USER"
SCRIPT
echo "Running script:"
bash /home/yusra/first_script.sh
rm -f /home/yusra/first_script.sh
echo "Q22 done"