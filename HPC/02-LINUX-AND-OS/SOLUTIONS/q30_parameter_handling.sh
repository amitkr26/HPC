#!/bin/bash
echo "=== Q30: Advanced Parameter Handling ==="
cat > /home/yusra/q30_script.sh << 'SCRIPT'
#!/bin/bash
echo "Number of parameters: $#"
echo "All parameters: $@"
echo "Script name: $0"
echo "First parameter: $1"
echo "Second parameter: $2"
SCRIPT
echo "Running script with params alpha beta gamma:"
bash /home/yusra/q30_script.sh alpha beta gamma
rm -f /home/yusra/q30_script.sh
echo "Q30 done"