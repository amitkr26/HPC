#!/bin/bash
echo "=== Q18: Custom Search Utilities with grep, find, and diff ==="
echo "--- search config files ---"
find /etc -name "*.conf" 2>/dev/null | head -3 | xargs grep -l "example" 2>/dev/null || echo "No matches"
echo "--- compare backups ---"
echo "Creating sample files for diff:"
echo "backup version 1" > /home/yusra/backup1.txt
echo "backup version 2" > /home/yusra/backup2.txt
diff /home/yusra/backup1.txt /home/yusra/backup2.txt
rm -f /home/yusra/backup1.txt /home/yusra/backup2.txt
echo "Q18 done"