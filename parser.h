#ifndef MYSH_PARSER_H
#define MYSH_PARSER_H

#include <stddef.h>

typedef enum {
    TOKEN_WORD,
    TOKEN_PIPE,
    TOKEN_REDIRECT_IN,
    TOKEN_REDIRECT_OUT,
    TOKEN_REDIRECT_APPEND,
    TOKEN_SEMICOLON,
    TOKEN_AMPERSAND
} TokenType;

typedef struct {
    TokenType type;
    char *text;
    unsigned char *expansion_mask;
} Token;

typedef struct {
    Token *items;
    size_t count;
    size_t capacity;
} TokenList;

typedef enum {
    PARSE_STATUS_OK = 0,
    PARSE_STATUS_RESOURCE_ERROR = 1,
    PARSE_STATUS_SYNTAX_ERROR = 2
} ParseStatus;

typedef struct {
    ParseStatus status;
    char message[128];
} ParseError;

void token_list_init(TokenList *tokens);
void token_list_free(TokenList *tokens);

ParseStatus tokenize(const char *line, TokenList *tokens, ParseError *error);
ParseStatus validate_syntax(const TokenList *tokens, ParseError *error);
ParseStatus parse_line(const char *line, TokenList *tokens, ParseError *error);

#endif
