#!/bin/bash
echo "=== Q36: Nano: Opening, Inserting, Saving, and Quitting ==="
echo "Testing text for nano"
echo "Nano test content" > /home/yusra/q37_file.txt
echo "Now opening with nano (Ctrl+O to save, Ctrl+X to quit)..."
nano /home/yusra/q37_file.txt
echo "After nano - content:"
cat /home/yusra/q37_file.txt
rm -f /home/yusra/q37_file.txt
echo "Q37 done"