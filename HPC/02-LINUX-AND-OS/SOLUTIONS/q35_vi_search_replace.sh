#!/bin/bash
echo "=== Q34: Vi: Searching and Replacing ==="
echo "Creating file with search test text..."
echo "The quick brown fox jumps over the lazy dog" > /home/yusra/q35_file.txt
echo "Search forward and replace:"
vi /home/yusra/q35_file.txt << 'SR'
/fox
S
The quick brown cat jumps over the lazy dog
:noh
:%s/dog/cat/g
:wq
SR
echo "After vi search & replace - content:"
cat /home/yusra/q35_file.txt
rm -f /home/yusra/q35_file.txt
echo "Q35 done"