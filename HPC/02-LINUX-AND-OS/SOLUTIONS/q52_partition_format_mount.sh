#!/bin/bash
echo "=== Q52: Partition, Format, and Mount ==="
echo "--- lsblk ---"
lsblk
echo "--- fdisk (simulated, not actually running) ---"
echo "fdisk would be used to create a new partition"
echo "--- mkfs.ext4 ---"
echo "mkfs.ext4 would format the partition"
echo "--- mount ---"
mkdir -p /mnt/labdisk
echo "mount -t ext4 /dev/sdb1 /mnt/labdisk would mount it"
echo "Q52 done"