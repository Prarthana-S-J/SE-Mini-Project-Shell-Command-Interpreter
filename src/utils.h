/*
 * utils.h - Shared helpers (memory, error reporting, string buffer).
 * Owner: Member 4 (Integration / Error handling)
 */
#ifndef UTILS_H
#define UTILS_H

#include <stddef.h>

#define SHELL_NAME    "mysh"
#define SHELL_VERSION "1.0"

/* Allocation wrappers: abort with a message if memory is exhausted. */
void *xmalloc(size_t size);
void *xrealloc(void *ptr, size_t size);
char *xstrdup(const char *s);

/* Print "mysh: <message>" to stderr (printf-style, newline appended). */
void shell_error(const char *fmt, ...);

/* Identifier helpers used for environment handling. */
int is_valid_name(const char *s, size_t len);   /* [A-Za-z_][A-Za-z0-9_]* */
int is_assignment(const char *word);            /* NAME=VALUE             */

/* Growable string buffer. */
typedef struct {
    char  *data;
    size_t len;
    size_t cap;
} StrBuf;

void  sb_init(StrBuf *sb);
void  sb_putc(StrBuf *sb, char c);
void  sb_putn(StrBuf *sb, const char *s, size_t n);
void  sb_puts(StrBuf *sb, const char *s);
char *sb_take(StrBuf *sb);   /* returns NUL-terminated heap string, resets sb */
void  sb_free(StrBuf *sb);

/* Heap copy of s[0..n) with leading/trailing blanks removed. */
char *str_trim_dup(const char *s, size_t n);

#endif /* UTILS_H */
