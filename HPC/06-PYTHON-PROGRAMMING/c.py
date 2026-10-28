import os

filename = "temp.txt"

# 1. Check if the file exists
if os.path.exists(filename):
    
    # 2. Read the content safely
    with open(filename, "r") as f:
        content = f.read()
        print("--- File Content ---")
        print(content)
        
    # 3. Delete the file
    os.remove(filename)
    print(f"\nSuccess: '{filename}' was read and deleted.")
    
else:
    print(f"Notice: '{filename}' does not exist.")