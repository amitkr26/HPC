# Debugging: File Handling

## Common Errors

### 1. Not checking if file opened
```c
FILE *fp = fopen("file.txt", "r");
char ch = fgetc(fp);  // CRASH if file doesn't exist
```
**Fix:** Check for NULL: `if(fp == NULL) { /* handle */ }`

### 2. Forgetting to close file
```c
void writeToFile(void) {
    FILE *fp = fopen("file.txt", "w");
    fprintf(fp, "data");
    // forgot fclose!
}
```
**Fix:** Always call `fclose(fp)`.

### 3. Using wrong mode
```c
FILE *fp = fopen("file.txt", "r");
fprintf(fp, "data");  // Error! Can't write in "r" mode
```

### 4. Reading after EOF
```c
while(!feof(fp)) {
    char ch = fgetc(fp);
    printf("%c", ch);  // Last char printed twice!
}
```
**Fix:** Check return value: `while((ch = fgetc(fp)) != EOF)`

### 5. Buffer overflow with fgets
```c
char buf[10];
fgets(buf, 100, fp);  // Reads up to 99 chars into 10-byte buffer!
```
**Fix:** `fgets(buf, sizeof(buf), fp);`

### 6. Not opening in binary mode for binary files
```c
FILE *fp = fopen("data.bin", "r");  // Should be "rb"
```

## Debugging Tips
- Always check fopen return value
- Print file operations during development
- Verify file exists before reading
- Use proper mode for read/write/append
- Close files in error paths too
