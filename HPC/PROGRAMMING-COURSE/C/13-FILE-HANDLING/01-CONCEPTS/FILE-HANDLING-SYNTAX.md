# Syntax: File Handling

## Include Header
```c
#include <stdio.h>
```

## Open File
```c
FILE *fp = fopen("file.txt", "r");
```

## Close File
```c
fclose(fp);
```

## Read Character
```c
int ch = fgetc(fp);
```

## Write Character
```c
fputc('A', fp);
```

## Read String
```c
char buf[100];
fgets(buf, 100, fp);
```

## Write String
```c
fputs("Hello\n", fp);
```

## Formatted Write
```c
fprintf(fp, "%s %d\n", str, num);
```

## Formatted Read
```c
fscanf(fp, "%s %d", str, &num);
```

## File Position
```c
fseek(fp, offset, origin);  // SEEK_SET, SEEK_CUR, SEEK_END
long pos = ftell(fp);
rewind(fp);
```

## Check End of File
```c
while(!feof(fp)) { ... }
```

## Complete Pattern
```c
FILE *fp = fopen("file.txt", "w");
if(fp == NULL) { printf("Error\n"); return 1; }
// operations
fclose(fp);
```
