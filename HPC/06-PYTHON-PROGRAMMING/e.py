import os

dir_name = "logs"

if os.path.exists(dir_name):
    # os.listdir returns an empty list if there are no files
    if not os.listdir(dir_name): 
        os.rmdir(dir_name)
        print(f"Success: Directory '{dir_name}' deleted.")
    else:
        print(f"Warning: Directory '{dir_name}' is not empty. Deletion aborted.")
else:
    print(f"Notice: Directory '{dir_name}' does not exist.")