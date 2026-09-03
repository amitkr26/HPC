#!/bin/bash
echo "=== Q11: Advanced File and Directory Management ==="
mkdir -p /home/yusra/q11_nested/a/b/c
echo "Created nested directories"
ls -lR /home/yusra/q11_nested
echo "--- recursive copy ---"
cp -rv /home/yusra/q11_nested/a /home/yusra/q11_copy
echo "--- find and delete ---"
find /home/yusra -name "q11_nested" -type d -exec rm -rf {} +
echo "After deletion:"
ls /home/yusra/ | grep q11