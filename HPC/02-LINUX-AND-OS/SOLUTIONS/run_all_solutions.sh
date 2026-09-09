#!/bin/bash
echo "=== Q3: File Compression and Archiving ==="
echo "Test content for gzip" > testfile.txt
cat testfile.txt
echo "---"
gzip testfile.txt
ls -l testfile.txt*
echo "---"
gzip -d testfile.txt.gz
cat testfile.txt
rm -f testfile.txt
echo "mkdir -p dir1 dir2" > /dev/null
echo "echo "file1"" > dir1/a.txt
echo "echo "file2"" > dir2/b.txt
tar -cvf archive.tar dir1 dir2
echo "---"
mkdir -p extract_dir
tar -xvf archive.tar -C extract_dir
ls extract_dir/
rm -rf dir1 dir2 extract_dir archive.tar testfile.txt.gz testfile.txt