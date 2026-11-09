"""
Master runner for all Data Visualization Mastery Lab activities.
Executes Activity 1, Activity 2, and Activity 3.
"""

import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

scripts = [
    ("Activity 1: Video Game Sales", os.path.join(BASE_DIR, "activity1_videogames.py")),
    ("Activity 2: Pokemon with Stats", os.path.join(BASE_DIR, "activity2_pokemon.py")),
    ("Activity 3: Telco Customer Churn", os.path.join(BASE_DIR, "activity3_telco_churn.py"))
]

print("================================================================================")
print("   DATA VISUALIZATION MASTERY LAB - GROUP 1 EXECUTION RUNNER")
print("   Members: Mehul Lahot | Raidas Kunal | Amit Kumar")
print("================================================================================\n")

for title, script in scripts:
    print(f">>> Running {title}...")
    result = subprocess.run([sys.executable, script], capture_output=True, text=True)
    if result.returncode == 0:
        print(f" [PASS] {title} completed successfully.\n")
    else:
        print(f" [FAIL] {title} encountered an error:")
        print(result.stderr)
        sys.exit(result.returncode)

print("All activities completed successfully! Check the outputs directory for plots.")

