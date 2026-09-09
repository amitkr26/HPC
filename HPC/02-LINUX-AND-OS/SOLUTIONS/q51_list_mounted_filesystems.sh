#!/bin/bash
echo "=== Q51: List Mounted File Systems ==="
df -Th
echo "--- Identify file systems ---"
df -Th | grep -E "ext4|tmpfs|overlay"
echo "Q51 done"