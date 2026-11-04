#!/bin/bash
echo "=== Q26: Log File Searcher Script ==="
cat > /home/yusra/q26_script.sh << 'SCRIPT'
#!/bin/bash
echo "Enter search string:"
read search_str
echo "Searching for '$search_str' in .log files:"
find /home/yusra -name "*.log" -type f 2>/dev/null | xargs grep -l "$search_str" 2>/dev/null || echo "No .log files found or no matches"
SCRIPT
echo "Running log search script (searching for 'user'):"
echo "user" | bash /home/yusra/q26_script.sh
rm -f /home/yusra/q26_script.sh
echo "Q26 done"