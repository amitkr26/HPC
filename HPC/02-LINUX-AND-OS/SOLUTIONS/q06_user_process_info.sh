#!/bin/bash
echo "=== Q6: User and Process Information ==="
echo "whoami:"
whoami
echo "who:"
who | head -3
echo "w:"
w | head -5
echo "ps:"
ps -e | head -5
echo "Q6 done"