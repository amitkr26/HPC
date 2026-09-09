#include <stdio.h>
#include <string.h>

struct Book {
    char title[50];
    char author[50];
    int issued;
};

void addBook(struct Book *b);
void displayBooks(struct Book *b, int count);
void searchBook(struct Book *b, int count, char *title);

int main() {
    struct Book books[20];
    int count = 0;
    int choice;
    char search[50];

    do {
        printf("\n---LIBRARY MANAGEMENT----\n");
        printf("1. Add Book\n");
        printf("2. Display Books\n");
        printf("3. Search Book\n");
        printf("4. Exit\n");
        printf("Enter choice: ");
        scanf("%d", &choice);

        switch (choice) {
        case 1:
            addBook(&books[count]);
            count++;
            break;
        case 2:
            displayBooks(books, count);
            break;
        case 3:
            printf("Enter title to search: ");
            scanf("%s", search);
            searchBook(books, count, search);
            break;
        case 4:
            printf("Exiting...\n");
            break;
        default:
            printf("Invalid choice!\n");
        }
    } while (choice != 4);

    return 0;
}

void addBook(struct Book *b) {
    printf("Enter title: ");
    scanf("%s", b->title);
    printf("Enter author: ");
    scanf("%s", b->author);
    b->issued = 0;
    printf("Book added.\n");
}

void displayBooks(struct Book *b, int count) {
    int i;

    if (count == 0) {
        printf("No books found.\n");
        return;
    }

    for (i = 0; i < count; i++) {
        printf("Title: %s, Author: %s, Issued: %s\n",
               b[i].title, b[i].author, b[i].issued ? "Yes" : "No");
    }
}

void searchBook(struct Book *b, int count, char *title) {
    int i;

    for (i = 0; i < count; i++) {
        if (strcmp(b[i].title, title) == 0) {
            printf("Book Found!\n");
            printf("Title: %s, Author: %s\n", b[i].title, b[i].author);
            return;
        }
    }

    printf("Book not found.\n");
}
