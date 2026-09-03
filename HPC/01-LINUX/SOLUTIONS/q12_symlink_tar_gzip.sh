#!/bin/bash
echo "=== Q12: File Linking, Archiving, and Compression ==="
echo "Create symbolic link:"
ln -s /home/yusra/q2_file.txt /home/yusra/q12_symlink
ls -la /home/yusra/q12_symlink
echo "--- combine tar with gzip ---"
tar -czf /home/yusra/q12_archive.tar.gz /home/yusra/q2_file.txt
echo "Created archive"
echo "--- inline extraction ---"
mkdir -p /home/yusra/q12_extract
tar -xzf /home/yusra/q12_archive.tar.gz -C /home/yusra/q12_extract
echo "Extracted to:"
ls /home/yusra/q12_extract/
rm -f /home/yusra/q12_symlink /home/yusra/q12_archive.tar.gz
rm -rf /home/yusra/q12_extract
echo "Q12 done"