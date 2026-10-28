#context manager auto-close files
with open("data.txt", "w") as f:
  f.write("hello, file System\n")
with open("data.txt", "r") as f:
  content = f.read()