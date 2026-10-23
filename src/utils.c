/*
 * utils.c - Shared helpers (memory, error reporting, string buffer).
 * Owner: Member 4 (Integration / Error handling)
 */
#include "utils.h"

#include <ctype.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void *xmalloc(size_t size)
{
    void *p = malloc(size ? size : 1);
    if (!p) {
        fprintf(stderr, SHELL_NAME ": out of memory\n");
        exit(1);
    }
    return p;
}

void *xrealloc(void *ptr, size_t size)
{
    void *p = realloc(ptr, size ? size : 1);
    if (!p) {
        fprintf(stderr, SHELL_NAME ": out of memory\n");
        exit(1);
    }
    return p;
}

char *xstrdup(const char *s)
{
    size_t n = strlen(s) + 1;
    char *p = xmalloc(n);
    memcpy(p, s, n);
    return p;
}

void shell_error(const char *fmt, ...)
{
    va_list ap;
    fflush(stdout);
    fprintf(stderr, SHELL_NAME ": ");
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
    fputc('\n', stderr);
}

int is_valid_name(const char *s, size_t len)
{
    size_t i;
    if (len == 0 || !(isalpha((unsigned char)s[0]) || s[0] == '_'))
        return 0;
    for (i = 1; i < len; i++)
        if (!(isalnum((unsigned char)s[i]) || s[i] == '_'))
            return 0;
    return 1;
}

int is_assignment(const char *word)
{
    const char *eq = strchr(word, '=');
    return eq != NULL && is_valid_name(word, (size_t)(eq - word));
}

void sb_init(StrBuf *sb)
{
    sb->cap = 32;
    sb->len = 0;
    sb->data = xmalloc(sb->cap);
    sb->data[0] = '\0';
}

static void sb_reserve(StrBuf *sb, size_t extra)
{
    if (sb->len + extra + 1 > sb->cap) {
        while (sb->len + extra + 1 > sb->cap)
            sb->cap *= 2;
        sb->data = xrealloc(sb->data, sb->cap);
    }
}

void sb_putc(StrBuf *sb, char c)
{
    sb_reserve(sb, 1);
    sb->data[sb->len++] = c;
    sb->data[sb->len] = '\0';
}

void sb_putn(StrBuf *sb, const char *s, size_t n)
{
    sb_reserve(sb, n);
    memcpy(sb->data + sb->len, s, n);
    sb->len += n;
    sb->data[sb->len] = '\0';
}

void sb_puts(StrBuf *sb, const char *s)
{
    sb_putn(sb, s, strlen(s));
}

char *sb_take(StrBuf *sb)
{
    char *p = sb->data;
    sb->data = NULL;
    sb->len = sb->cap = 0;
    return p;
}

void sb_free(StrBuf *sb)
{
    free(sb->data);
    sb->data = NULL;
    sb->len = sb->cap = 0;
}

char *str_trim_dup(const char *s, size_t n)
{
    char *out;
    while (n > 0 && (*s == ' ' || *s == '\t' || *s == '\n' || *s == '\r')) {
        s++;
        n--;
    }
    while (n > 0 && (s[n - 1] == ' ' || s[n - 1] == '\t' ||
                     s[n - 1] == '\n' || s[n - 1] == '\r'))
        n--;
    out = xmalloc(n + 1);
    memcpy(out, s, n);
    out[n] = '\0';
    return out;
}
