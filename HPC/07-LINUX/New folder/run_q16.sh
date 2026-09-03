#!/bin/bash
echo "=== Q16: Working with Streams and Redirection ==="
echo "--- multi-line strings ---"
echo -e "line1\nline2\nline3"
echo "--- tac ---"
echo -e "line1\nline2\nline3" | tac
echo "--- zcat and grep ---"
echo "Test content for gzip testing" > /home/yusra/q16_file.txt.gz.uncompressed
echo "Some data here" >> /home/yusra/q16_file.txt.gz.uncompressed
# Create gzip first
gzip -c /home/yusra/q16_file.txt.gz.uncompressed > /home/yusra/q16_file.txt.gz
echo "From compressed archive:"
zcat /home/yusra/q16_file.txt.gz | grep "data"
rm -f /home/yusra/q16_file.txt.gz /home/yusra/q16_file.txt.gz.uncompressed
echo "Q16 done"