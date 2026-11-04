#!/bin/bash
echo "=== Q28: Age Calculator ==="
cat > /home/yusra/q28_script.sh << 'SCRIPT'
#!/bin/bash
echo "Enter birth year:"
read birth_year
current_year=2026
age=$((current_year - birth_year))
echo "You are $age years old (approx)."
SCRIPT
echo "Running with birth year 1990:"
echo "1990" | bash /home/yusra/q28_script.sh
echo "Running with birth year 2005:"
echo "2005" | bash /home/yusra/q28_script.sh
rm -f /home/yusra/q28_script.sh
echo "Q28 done"