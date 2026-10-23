/*
 * parser.h - Tokenizer / command-line parser.
 * Owner: Member 2 (Parser, tokenization, expansion)
 *
 * The parser consumes ONE pipeline at a time from a line of input. A pipeline
 * ends at ';', '&', a newline or the end of the string. Parsing one pipeline at
 * a time means variable expansion for a later pipeline sees the effects of an
 * earlier one, e.g.  "export X=1; echo $X"  prints 1.
 */
#ifndef PARSER_H
#define PARSER_H

#include <stddef.h>

typedef struct {
    char **argv;      /* NULL-terminated argument vector            */
    int    argc;
    char  *infile;    /* '<'  target or NULL                        */
    char  *outfile;   /* '>' or '>>' target or NULL                 */
    int    append;    /* 1 if outfile was given with '>>'           */
} Command;

typedef struct {
    Command *cmds;    /* cmd[0] | cmd[1] | ... | cmd[ncmds-1]       */
    int      ncmds;
    int      background;  /* 1 if terminated by '&'                 */
    char    *text;    /* trimmed source text of the pipeline        */
} Pipeline;

typedef enum {
    PARSE_OK,         /* a pipeline was produced                    */
    PARSE_END,        /* no more input (blank line / comment only)  */
    PARSE_ERROR       /* syntax error; message written to errbuf    */
} ParseResult;

/*
 * Parse the next pipeline starting at *cursor. On PARSE_OK/PARSE_END *cursor
 * is advanced past the consumed text. On PARSE_ERROR *cursor is moved to the
 * end of the input (the rest of the line is discarded, as in POSIX shells).
 * last_status supplies the value of $?.
 */
ParseResult parse_next_pipeline(const char **cursor, int last_status,
                                Pipeline *out, char *errbuf, size_t errlen);

void pipeline_free(Pipeline *pl);

#endif /* PARSER_H */
