import os

dir_name = "backup_2026"

# 1. Create the new directory (with a safety check)
if not os.path.exists(dir_name):
    os.mkdir(dir_name)

# 2. Change the current working directory
os.chdir(dir_name)

# 3. Verify the move
print("Current Working Directory:", os.getcwd())