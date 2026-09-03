#!/bin/bash
echo "=== Q5: System Info and Utilities ==="
echo "Calendar:"
cal
echo "Date:"
date
echo "Calculation:"
echo "10 + 20 = $((10 + 20))"
echo "Banner (if available):"
banner "Linux Lab" 2>/dev/null || echo "banner not available"
echo "Q5 done"