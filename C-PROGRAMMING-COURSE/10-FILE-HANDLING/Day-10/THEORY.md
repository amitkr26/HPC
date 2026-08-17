# Theory: File Handling

## What is File Handling?
File handling allows programs to read from and write to files on disk.
This enables data to persist after the program ends.

## File Pointer (FILE*)
```c
FILE *fp;
```
A pointer to a structure that holds file information.

## Opening a File
```c
FILE *fp = fopen("filename.txt", "mode");
if(fp == NULL) {
    printf("Error opening file\n");
    return 1;
}
```

## File Modes
| Mode | Description |
|------|-------------|
| "r" | Read only (file must exist) |
| "w" | Write only (creates/truncates file) |
| "a" | Append (creates if doesn't exist) |
| "r+" | Read + Write (file must exist) |
| "w+" | Read + Write (creates/truncates) |
| "a+" | Read + Append (creates if doesn't exist) |

## Closing a File
```c
fclose(fp);
```
Always close files when done.

## Reading Characters
```c
char ch = fgetc(fp);     // read one character
while(ch != EOF) {
    printf("%c", ch);
    ch = fgetc(fp);
}
```

## Writing Characters
```c
fputc('A', fp);          // write one character
fputs("Hello\n", fp);   // write string
```

## Formatted I/O
```c
fprintf(fp, "Name: %s, Age: %d\n", name, age);
fscanf(fp, "%s %d", name, &age);
```

## Reading Lines
```c
char buffer[100];
fgets(buffer, 100, fp);  // reads until newline or 99 chars
```

## Random Access
```c
fseek(fp, 0, SEEK_SET);  // beginning
fseek(fp, 0, SEEK_END);  // end
fseek(fp, 10, SEEK_CUR); // 10 bytes forward
long pos = ftell(fp);     // current position
rewind(fp);               // go to beginning
```

## Error Handling
```c
if(feof(fp))    // end of file reached
if(ferror(fp))  // error occurred
```
