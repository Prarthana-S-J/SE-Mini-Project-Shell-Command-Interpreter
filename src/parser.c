/*
 * parser.c - Tokenizer / command-line parser.
 * Owner: Member 2 (Parser, tokenization, expansion)
 *
 * Grammar (informal):
 *   pipeline   := command ( '|' command )* [ '&' | ';' ]
 *   command    := ( WORD | redirect )+       (at least one WORD)
 *   redirect   := ( '<' | '>' | '>>' ) WORD
 *
 * Words support single quotes, double quotes, backslash escapes, and
 * expansion of $NAME, ${NAME}, $?, $$ and a leading ~ (outside single quotes).
 */
#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200809L
#endif

#include "parser.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "utils.h"

static int is_blank(char c) { return c == ' ' || c == '\t' || c == '\r'; }
static int is_meta(char c)
{
    return c == ';' || c == '>' || c == '<' || c == '|'
        || c == '&';
}
static int ends_word(char c){ return c == '\0' || c == '\n' || is_blank(c) ||
                                     is_meta(c); }

static void seterr(char *errbuf, size_t errlen, const char *msg)
{
    snprintf(errbuf, errlen, "%s", msg);
}

/* ---------- Command helpers ------------------------------------------- */

static void command_init(Command *c)
{
    c->argv = xmalloc(sizeof(char *));
    c->argv[0] = NULL;
    c->argc = 0;
    c->infile = c->outfile = NULL;
    c->append = 0;
}

static void command_add_arg(Command *c, char *word)
{
    c->argv = xrealloc(c->argv, (size_t)(c->argc + 2) * sizeof(char *));
    c->argv[c->argc++] = word;
    c->argv[c->argc] = NULL;
}

static int command_is_empty(const Command *c)
{
    return c->argc == 0 && c->infile == NULL && c->outfile == NULL;
}

static void command_free(Command *c)
{
    int i;
    for (i = 0; i < c->argc; i++)
        free(c->argv[i]);
    free(c->argv);
    free(c->infile);
    free(c->outfile);
    c->argv = NULL;
    c->infile = c->outfile = NULL;
}

void pipeline_free(Pipeline *pl)
{
    int i;
    for (i = 0; i < pl->ncmds; i++)
        command_free(&pl->cmds[i]);
    free(pl->cmds);
    free(pl->text);
    pl->cmds = NULL;
    pl->text = NULL;
    pl->ncmds = 0;
}

/* ---------- Expansion -------------------------------------------------- */


/*
 * Read one word starting at *pp. On success returns 0, sets *out to a heap
 * string (or NULL when an unquoted expansion produced an empty result and the
 * word must be dropped) and advances *pp. Returns -1 on error.
 */
static int expand_dollar(const char **pp, int last_status, StrBuf *sb,
                         char *errbuf, size_t errlen)
{
    const char *p = *pp;
    char tmp[32];

    if (p[1] == '?') {
        snprintf(tmp, sizeof tmp, "%d", last_status);
        sb_puts(sb, tmp);
        *pp = p + 2;
        return 0;
    }

    if (p[1] == '$') {
        snprintf(tmp, sizeof tmp, "%ld", (long)getpid());
        sb_puts(sb, tmp);
        *pp = p + 2;
        return 0;
    }

    if (p[1] == '{') {
        const char *close = strchr(p + 2, '}');
        const char *name_start = p + 2;
        size_t name_len;
        char *name;
        const char *value;

        if (close == NULL ||
            !is_valid_name(name_start, (size_t)(close - name_start))) {
            seterr(errbuf, errlen, "bad substitution");
            return -1;
        }

        name_len = (size_t)(close - name_start);
        name = xmalloc(name_len + 1);
        memcpy(name, name_start, name_len);
        name[name_len] = '\0';

        value = getenv(name);
        if (value != NULL)
            sb_puts(sb, value);

        free(name);
        *pp = close + 1;
        return 0;
    }

    if (isalpha((unsigned char)p[1]) || p[1] == '_') {
        const char *end = p + 1;
        size_t name_len;
        char *name;
        const char *value;

        while (isalnum((unsigned char)*end) || *end == '_')
            end++;

        name_len = (size_t)(end - (p + 1));
        name = xmalloc(name_len + 1);
        memcpy(name, p + 1, name_len);
        name[name_len] = '\0';

        value = getenv(name);
        if (value != NULL)
            sb_puts(sb, value);

        free(name);
        *pp = end;
        return 0;
    }

    /* A lone or unsupported '$' remains literal. */
    sb_putc(sb, '$');
    *pp = p + 1;
    return 0;
}

static int read_word(const char **pp, int last_status, char **out,
                     char *errbuf, size_t errlen)
{
    const char *p = *pp;
    StrBuf sb;
    int quoted = 0;
    int expansion_seen = 0;

    sb_init(&sb);

    /* Expand a leading ~ only when it stands alone or starts ~/path.
       ~user is deliberately unsupported. */
    if (*p == '~' &&
        (p[1] == '\0' || p[1] == '/' || p[1] == '\n' ||
         p[1] == ';' || p[1] == ' ' || p[1] == '\t' ||
         p[1] == '\r')) {
        const char *home = getenv("HOME");
        if (home != NULL) {
            sb_puts(&sb, home);
            p++;
            expansion_seen = 1;
        }
    }

    while (!ends_word(*p)) {
        if (*p == '\'') {
            quoted = 1;
            p++;

            while (*p && *p != '\'')
                sb_putc(&sb, *p++);

            if (!*p) {
                sb_free(&sb);
                seterr(errbuf, errlen,
                       "syntax error: unterminated single quote");
                return -1;
            }

            p++;
        } else if (*p == '"') {
            quoted = 1;
            p++;

            while (*p && *p != '"') {
                if (*p == '\\' &&
                    (p[1] == '"' || p[1] == '\\' || p[1] == '$')) {
                    sb_putc(&sb, p[1]);
                    p += 2;
                } else if (*p == '$') {
                    if (expand_dollar(&p, last_status, &sb,
                                      errbuf, errlen) < 0) {
                        sb_free(&sb);
                        return -1;
                    }
                    expansion_seen = 1;
                } else {
                    sb_putc(&sb, *p++);
                }
            }

            if (!*p) {
                sb_free(&sb);
                seterr(errbuf, errlen,
                       "syntax error: unterminated double quote");
                return -1;
            }

            p++;
        } else if (*p == '\\') {
            quoted = 1;

            if (p[1] != '\0' && p[1] != '\n') {
                sb_putc(&sb, p[1]);
                p += 2;
            } else {
                p++;
            }
        } else if (*p == '$') {
            if (expand_dollar(&p, last_status, &sb,
                              errbuf, errlen) < 0) {
                sb_free(&sb);
                return -1;
            }
            expansion_seen = 1;
        } else {
            sb_putc(&sb, *p++);
        }
    }

    *pp = p;

    if (sb.len == 0 && !quoted && expansion_seen) {
        sb_free(&sb);
        *out = NULL;
    } else {
        *out = sb_take(&sb);
    }

    return 0;
}


/* ---------- Pipeline parser ------------------------------------------- */

static void skip_to_end(const char **cursor)
{
    *cursor += strlen(*cursor);
}

static void fail(Pipeline *pl, Command *cur, const char **cursor,
                 char *errbuf, size_t errlen, const char *msg)
{
    if (msg)
        seterr(errbuf, errlen, msg);
    command_free(cur);
    pipeline_free(pl);
    skip_to_end(cursor);
}

static void pipeline_push(Pipeline *pl, Command *c, int *cap)
{
    if (pl->ncmds == *cap) {
        *cap *= 2;
        pl->cmds = xrealloc(pl->cmds, (size_t)*cap * sizeof(Command));
    }
    pl->cmds[pl->ncmds++] = *c;
}

ParseResult parse_next_pipeline(const char **cursor, int last_status,
                                Pipeline *pl, char *errbuf, size_t errlen)
{
    const char *p = *cursor;
    const char *start, *end = NULL;
    Command cur;
    int cap = 4;
    int pipe_pending = 0;
    char terminator = '\0';

    memset(pl, 0, sizeof *pl);
    errbuf[0] = '\0';

    /* Skip leading blanks, newlines and comments. */
    for (;;) {
        while (is_blank(*p) || *p == '\n')
            p++;
        if (*p == '#') {
            while (*p && *p != '\n')
                p++;
            continue;
        }
        break;
    }
    if (*p == '\0') {
        *cursor = p;
        return PARSE_END;
    }

    start = p;
    pl->cmds = xmalloc((size_t)cap * sizeof(Command));
    command_init(&cur);

    for (;;) {
        char c;
        while (is_blank(*p))
            p++;
        c = *p;

        if (c == '#') {                     /* comment to end of line */
            while (*p && *p != '\n')
                p++;
            continue;
        }

        if (c == '\0' || c == '\n' || c == ';') {
            end = p;
            terminator = c;
            if (c != '\0')
                p++;
            break;
        }

        /*
         * Handle pipeline separators.
         * Save the current command and begin parsing the next one.
         */
        if (c == '|') {
            if (cur.argc == 0) {
                fail(pl, &cur, cursor, errbuf, errlen,
                     "syntax error: missing command before '|'");
                return PARSE_ERROR;
            }

            pipeline_push(pl, &cur, &cap);
            command_init(&cur);

            p++;
            pipe_pending = 1;
            continue;
        }

        if (c == '<' || c == '>') {
            char *filename = NULL;
            char redirection = c;

            if (redirection == '<' && cur.infile != NULL) {
                fail(pl, &cur, cursor, errbuf, errlen,
                     "syntax error: duplicate input redirection");
                return PARSE_ERROR;
            }

            if (redirection == '>' && cur.outfile != NULL) {
                fail(pl, &cur, cursor, errbuf, errlen,
                     "syntax error: duplicate output redirection");
                return PARSE_ERROR;
            }

            p++;

            if (redirection == '>') {
                if (*p == '>') {
                    cur.append = 1;
                    p++;
                } else {
                    cur.append = 0;
                }
            }

            while (is_blank(*p))
                p++;

            if (read_word(&p, last_status, &filename,
                          errbuf, errlen) < 0) {
                fail(pl, &cur, cursor, errbuf, errlen, NULL);
                return PARSE_ERROR;
            }

            if (filename == NULL || filename[0] == '\0') {
                free(filename);
                fail(pl, &cur, cursor, errbuf, errlen,
                     redirection == '<'
                         ? "syntax error: expected filename after '<'"
                         : "syntax error: expected filename after '>'");
                return PARSE_ERROR;
            }

            if (redirection == '<')
                cur.infile = filename;
            else
                cur.outfile = filename;
        } else {
            /* ordinary word */
            char *word = NULL;

            if (read_word(&p, last_status, &word,
                          errbuf, errlen) < 0) {
                fail(pl, &cur, cursor, errbuf, errlen, NULL);
                return PARSE_ERROR;
            }

            if (word) {
                command_add_arg(&cur, word);
                pipe_pending = 0;
            }
        }
    }

    /* Finalise the last command of the pipeline. */
    if (command_is_empty(&cur)) {
        if (pl->ncmds == 0) {
            char msg[64];
            snprintf(msg, sizeof msg, "syntax error near unexpected token '%c'",
                     terminator ? terminator : ';');
            fail(pl, &cur, cursor, errbuf, errlen, msg);
        } else {
            fail(pl, &cur, cursor, errbuf, errlen,
                 "syntax error: missing command after '|'");
        }
        return PARSE_ERROR;
    }
    if (cur.argc == 0) {
        fail(pl, &cur, cursor, errbuf, errlen,
             "syntax error: redirection without a command");
        return PARSE_ERROR;
    }
    (void)pipe_pending;
    pipeline_push(pl, &cur, &cap);
    pl->text = str_trim_dup(start, (size_t)(end - start));
    *cursor = p;
    return PARSE_OK;
}
