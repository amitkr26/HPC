print("Enter text to append to the log. Type 'EXIT' to stop.")

# Open the file in append mode ("a")
with open("log.txt", "a") as f:
    while True:
        # Prompt the user for input
        user_text = input("> ")
        
        # Check for the exit command
        if user_text.upper() == 'EXIT':
            print("Logging stopped.")
            break
            
        # Write the text to the file and add a new line
        f.write(user_text + "\n")
        
        # Optional: flush ensures the data is written immediately 
        # instead of waiting in the memory buffer
        f.flush()