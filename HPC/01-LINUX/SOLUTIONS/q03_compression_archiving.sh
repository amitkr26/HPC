#!/bin/bash
echo "=== Q3: File Compression and Archiving ==="
echo "Test content" > /home/yusra/q3_file.txt
echo "Original:"
cat /home/yusra/q3_file.txt
echo "---gzip compress---"
gzip -c /home/yusra/q3_file.txt > /home/yusra/q3_file.txt.gz
ls -l /home/yusra/q3_file.txt*
echo "---gzip decompress---"
gzip -d -c /home/yusra/q3_file.txt.gz > /home/yusra/q3_file_restored.txt
echo "Restored:"
cat /home/yusra/q3_file_restored.txt
echo "---tar archive---"
mkdir -p /home/yusra/q3_dir1 /home/yusra/q3_dir2
echo "f1" > /home/yusra/q3_dir1/a.txt
echo "f2" > /home/yusra/q3_dir2/b.txt
tar -cvf /home/yusra/q3_archive.tar /home/yusra/q3_dir1 /home/yusra/q3_dir2
echo "---tar extract---"
mkdir -p /home/yusra/q3_extract
tar -xvf /home/yusra/q3_archive.tar -C /home/yusra/q3_extract
ls /home/yusra/q3_extract/
rm -f /home/yusra/q3_file.txt /home/yusra/q3_file.txt.gz /home/yusra/q3_file_restored.txt
rm -rf /home/yusra/q3_dir1 /home/yusra/q3_dir2 /home/yusra/q3_extract /home/yusra/q3_archive.tar
echo "Q3 done"