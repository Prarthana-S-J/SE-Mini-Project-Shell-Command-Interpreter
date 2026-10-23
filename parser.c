#include "parser.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    char *data;
    unsigned char *expansion_mask;
    size_t length;
    size_t capacity;
} WordBuilder;

static void set_error(ParseError *error, ParseStatus status, const char *message)
{
    if (error != NULL) {
        error->status = status;
        snprintf(error->message, sizeof(error->message), "%s", message);
    }
}

static void clear_error(ParseError *error)
{
    if (error != NULL) {
        error->status = PARSE_STATUS_OK;
        error->message[0] = '\0';
    }
}

static void clear_tokens(TokenList *tokens)
{
    size_t index;

    for (index = 0; index < tokens->count; ++index) {
        free(tokens->items[index].text);
        free(tokens->items[index].expansion_mask);
    }
    tokens->count = 0;
}

void token_list_init(TokenList *tokens)
{
    if (tokens != NULL) {
        tokens->items = NULL;
        tokens->count = 0;
        tokens->capacity = 0;
    }
}

void token_list_free(TokenList *tokens)
{
    if (tokens != NULL) {
        clear_tokens(tokens);
        free(tokens->items);
        token_list_init(tokens);
    }
}

static int reserve_tokens(TokenList *tokens, size_t needed)
{
    size_t capacity;
    Token *items;

    if (needed <= tokens->capacity) {
        return 1;
    }
    capacity = tokens->capacity == 0 ? 8 : tokens->capacity;
    while (capacity < needed) {
        if (capacity > SIZE_MAX / 2) {
            return 0;
        }
        capacity *= 2;
    }
    if (capacity > SIZE_MAX / sizeof(*items)) {
        return 0;
    }
    items = (Token *)realloc(tokens->items, capacity * sizeof(*items));
    if (items == NULL) {
        return 0;
    }
    tokens->items = items;
    tokens->capacity = capacity;
    return 1;
}

static int append_token(TokenList *tokens, TokenType type, char *text,
                        unsigned char *expansion_mask)
{
    if (!reserve_tokens(tokens, tokens->count + 1)) {
        free(text);
        free(expansion_mask);
        return 0;
    }
    tokens->items[tokens->count].type = type;
    tokens->items[tokens->count].text = text;
    tokens->items[tokens->count].expansion_mask = expansion_mask;
    ++tokens->count;
    return 1;
}

static int reserve_word(WordBuilder *word, size_t needed)
{
    size_t capacity;
    char *data;
    unsigned char *expansion_mask;

    if (needed <= word->capacity) {
        return 1;
    }
    capacity = word->capacity == 0 ? 16 : word->capacity;
    while (capacity < needed) {
        if (capacity > SIZE_MAX / 2) {
            return 0;
        }
        capacity *= 2;
    }
    data = (char *)realloc(word->data, capacity);
    if (data == NULL) {
        return 0;
    }
    word->data = data;
    expansion_mask =
        (unsigned char *)realloc(word->expansion_mask, capacity);
    if (expansion_mask == NULL) {
        return 0;
    }
    word->expansion_mask = expansion_mask;
    word->capacity = capacity;
    return 1;
}

static int append_character(WordBuilder *word, char character,
                            int expansion_allowed)
{
    if (word->length > SIZE_MAX - 2 ||
        !reserve_word(word, word->length + 2)) {
        return 0;
    }
    word->data[word->length++] = character;
    word->data[word->length] = '\0';
    word->expansion_mask[word->length - 1] =
        expansion_allowed ? 1U : 0U;
    return 1;
}

static int finish_word(TokenList *tokens, WordBuilder *word, int *word_started)
{
    char *text;
    unsigned char *expansion_mask;

    if (!*word_started) {
        return 1;
    }
    text = (char *)malloc(word->length + 1);
    if (text == NULL) {
        return 0;
    }
    expansion_mask =
        (unsigned char *)malloc(word->length + 1);
    if (expansion_mask == NULL) {
        free(text);
        return 0;
    }
    if (word->length != 0) {
        memcpy(text, word->data, word->length);
        memcpy(expansion_mask, word->expansion_mask, word->length);
    }
    text[word->length] = '\0';
    expansion_mask[word->length] = 0U;
    if (!append_token(tokens, TOKEN_WORD, text, expansion_mask)) {
        return 0;
    }
    word->length = 0;
    if (word->data != NULL) {
        word->data[0] = '\0';
    }
    *word_started = 0;
    return 1;
}

static int is_space(char character)
{
    return character == ' ' || character == '\t' || character == '\n' ||
           character == '\r' || character == '\v' || character == '\f';
}

static int is_operator(char character)
{
    return character == '|' || character == '<' || character == '>' ||
           character == ';' || character == '&';
}

static int append_operator(TokenList *tokens, TokenType type)
{
    return append_token(tokens, type, NULL, NULL);
}

static int has_closing_brace(const char *line, size_t start, char quote)
{
    size_t index;

    for (index = start; line[index] != '\0'; ++index) {
        if (line[index] == '}') {
            return 1;
        }
        if (is_space(line[index]) ||
            (quote == '\0' && (line[index] == '\'' || line[index] == '"' ||
                               is_operator(line[index]))) ||
            (quote != '\0' && line[index] == quote)) {
            return 0;
        }
    }
    return 0;
}

ParseStatus tokenize(const char *line, TokenList *tokens, ParseError *error)
{
    size_t index = 0;
    char quote = '\0';
    int word_started = 0;
    WordBuilder word = {NULL, NULL, 0, 0};
    ParseStatus status = PARSE_STATUS_OK;

    if (line == NULL || tokens == NULL) {
        set_error(error, PARSE_STATUS_RESOURCE_ERROR, "invalid tokenizer input");
        return PARSE_STATUS_RESOURCE_ERROR;
    }
    clear_tokens(tokens);
    clear_error(error);

    while (line[index] != '\0') {
        char character = line[index];

        if (quote == '\'') {
            if (character == '\'') {
                quote = '\0';
            } else if (!append_character(&word, character, 0)) {
                status = PARSE_STATUS_RESOURCE_ERROR;
                set_error(error, status, "out of memory");
                goto failed;
            }
            ++index;
            continue;
        }
        if (quote == '"') {
            int expansion_allowed = 1;

            if (character == '"') {
                quote = '\0';
                ++index;
                continue;
            }
            if (character == '\\') {
                if (line[index + 1] == '\0') {
                    status = PARSE_STATUS_SYNTAX_ERROR;
                    set_error(error, status, "trailing escape");
                    goto failed;
                }
                character = line[index + 1];
                index += 2;
                expansion_allowed = 0;
            } else {
                if (character == '$' && line[index + 1] == '{' &&
                    !has_closing_brace(line, index + 2, quote)) {
                    status = PARSE_STATUS_SYNTAX_ERROR;
                    set_error(error, status, "bad substitution");
                    goto failed;
                }
                ++index;
            }
            if (!append_character(&word, character, expansion_allowed)) {
                status = PARSE_STATUS_RESOURCE_ERROR;
                set_error(error, status, "out of memory");
                goto failed;
            }
            continue;
        }

        if (character == '#') {
            if (!word_started) {
                break;
            }
            if (!append_character(&word, character, 1)) {
                status = PARSE_STATUS_RESOURCE_ERROR;
                set_error(error, status, "out of memory");
                goto failed;
            }
            ++index;
            continue;
        }
        if (is_space(character)) {
            if (!finish_word(tokens, &word, &word_started)) {
                status = PARSE_STATUS_RESOURCE_ERROR;
                set_error(error, status, "out of memory");
                goto failed;
            }
            ++index;
            continue;
        }
        if (character == '\'' || character == '"') {
            word_started = 1;
            quote = character;
            ++index;
            continue;
        }
        if (character == '\\') {
            if (line[index + 1] == '\0') {
                status = PARSE_STATUS_SYNTAX_ERROR;
                set_error(error, status, "trailing escape");
                goto failed;
            }
            word_started = 1;
            if (!append_character(&word, line[index + 1], 0)) {
                status = PARSE_STATUS_RESOURCE_ERROR;
                set_error(error, status, "out of memory");
                goto failed;
            }
            index += 2;
            continue;
        }
        if (character == '$' && line[index + 1] == '{' &&
            !has_closing_brace(line, index + 2, '\0')) {
            status = PARSE_STATUS_SYNTAX_ERROR;
            set_error(error, status, "bad substitution");
            goto failed;
        }
        if ((character == '&' && line[index + 1] == '&') ||
            (character == '|' && line[index + 1] == '|')) {
            status = PARSE_STATUS_SYNTAX_ERROR;
            set_error(error, status,
                      character == '&' ? "&& is not supported" :
                                         "|| is not supported");
            goto failed;
        }
        if (is_operator(character)) {
            TokenType type;

            if (!finish_word(tokens, &word, &word_started)) {
                status = PARSE_STATUS_RESOURCE_ERROR;
                set_error(error, status, "out of memory");
                goto failed;
            }
            switch (character) {
            case '|':
                type = TOKEN_PIPE;
                ++index;
                break;
            case '<':
                type = TOKEN_REDIRECT_IN;
                ++index;
                break;
            case '>':
                if (line[index + 1] == '>') {
                    type = TOKEN_REDIRECT_APPEND;
                    index += 2;
                } else {
                    type = TOKEN_REDIRECT_OUT;
                    ++index;
                }
                break;
            case ';':
                type = TOKEN_SEMICOLON;
                ++index;
                break;
            default:
                type = TOKEN_AMPERSAND;
                ++index;
                break;
            }
            if (!append_operator(tokens, type)) {
                status = PARSE_STATUS_RESOURCE_ERROR;
                set_error(error, status, "out of memory");
                goto failed;
            }
            continue;
        }
        word_started = 1;
        if (!append_character(&word, character, 1)) {
            status = PARSE_STATUS_RESOURCE_ERROR;
            set_error(error, status, "out of memory");
            goto failed;
        }
        ++index;
    }

    if (quote != '\0') {
        status = PARSE_STATUS_SYNTAX_ERROR;
        set_error(error, status,
                  quote == '\'' ? "unterminated single quote" :
                                  "unterminated double quote");
        goto failed;
    }
    if (!finish_word(tokens, &word, &word_started)) {
        status = PARSE_STATUS_RESOURCE_ERROR;
        set_error(error, status, "out of memory");
        goto failed;
    }
    free(word.data);
    free(word.expansion_mask);
    return PARSE_STATUS_OK;

failed:
    free(word.data);
    free(word.expansion_mask);
    clear_tokens(tokens);
    return status;
}

static int is_redirection(TokenType type)
{
    return type == TOKEN_REDIRECT_IN || type == TOKEN_REDIRECT_OUT ||
           type == TOKEN_REDIRECT_APPEND;
}

static ParseStatus syntax_error(ParseError *error, const char *message)
{
    set_error(error, PARSE_STATUS_SYNTAX_ERROR, message);
    return PARSE_STATUS_SYNTAX_ERROR;
}

ParseStatus validate_syntax(const TokenList *tokens, ParseError *error)
{
    size_t index;
    int stage_has_command = 0;
    int pipeline_has_tokens = 0;
    int after_pipe = 0;
    int needs_redirection_target = 0;

    if (tokens == NULL) {
        set_error(error, PARSE_STATUS_RESOURCE_ERROR, "invalid token list");
        return PARSE_STATUS_RESOURCE_ERROR;
    }
    clear_error(error);

    for (index = 0; index < tokens->count; ++index) {
        const Token *token = &tokens->items[index];

        if (token->type == TOKEN_WORD) {
            if (needs_redirection_target) {
                if (token->text == NULL || token->text[0] == '\0') {
                    return syntax_error(error, "missing file name");
                }
                needs_redirection_target = 0;
            } else {
                stage_has_command = 1;
            }
            pipeline_has_tokens = 1;
            continue;
        }
        if (is_redirection(token->type)) {
            if (needs_redirection_target) {
                return syntax_error(error, "missing file name");
            }
            needs_redirection_target = 1;
            pipeline_has_tokens = 1;
            continue;
        }
        if (token->type == TOKEN_PIPE) {
            if (needs_redirection_target) {
                return syntax_error(error, "missing file name");
            }
            if (!stage_has_command) {
                return syntax_error(error, after_pipe || !pipeline_has_tokens
                                               ? "empty pipeline stage"
                                               : "redirection without a command");
            }
            stage_has_command = 0;
            pipeline_has_tokens = 1;
            after_pipe = 1;
            continue;
        }
        if (token->type == TOKEN_SEMICOLON ||
            token->type == TOKEN_AMPERSAND) {
            if (needs_redirection_target) {
                return syntax_error(error, "missing file name");
            }
            if (pipeline_has_tokens && !stage_has_command) {
                return syntax_error(error, after_pipe
                                               ? "empty pipeline stage"
                                               : "redirection without a command");
            }
            stage_has_command = 0;
            pipeline_has_tokens = 0;
            after_pipe = 0;
        }
    }

    if (needs_redirection_target) {
        return syntax_error(error, "missing file name");
    }
    if (pipeline_has_tokens && !stage_has_command) {
        return syntax_error(error, after_pipe ? "empty pipeline stage"
                                             : "redirection without a command");
    }
    return PARSE_STATUS_OK;
}

ParseStatus parse_line(const char *line, TokenList *tokens, ParseError *error)
{
    ParseStatus status = tokenize(line, tokens, error);

    if (status != PARSE_STATUS_OK) {
        return status;
    }
    status = validate_syntax(tokens, error);
    if (status != PARSE_STATUS_OK) {
        clear_tokens(tokens);
    }
    return status;
}
