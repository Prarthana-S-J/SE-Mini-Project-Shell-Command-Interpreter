/*
 * test_parser.c - Unit tests for the parser and utility helpers.
 * Owner: Member 4 (Testing)
 *
 * Build/run:  make unit-test
 * Output line format:  <ID> <REQ> PASS|FAIL <description>
 */
#include "../parser.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "parser.h"
#include "utils.h"

static int failures = 0;
static int total = 0;
static int skipped = 0;

/* tests/enabled_tests.txt lists the test IDs that must pass at the current development stage
 * (see stories/README.md); the others are reported as SKIP. "ALL" (or a missing file) enables everything. */
static int enabled(const char *id)
{
    char line[64];
    FILE *f;
    int found = 0;

    if (getenv("MYSH_ENABLE_ALL"))
        return 1;
    f = fopen(getenv("MYSH_ENABLED_FILE") ? getenv("MYSH_ENABLED_FILE") : "tests/enabled_tests.txt", "r");
    if (!f)
        return 1;
    while (fgets(line, sizeof line, f)) {
        line[strcspn(line, "\r\n")] = '\0';
        if (strcmp(line, "ALL") == 0 || strcmp(line, id) == 0) {
            found = 1;
            break;
        }
    }
    fclose(f);
    return found;
}

static void report(const char *id, const char *req, int ok, const char *desc)
{
    if (!enabled(id)) {
        skipped++;
        printf("%s %s SKIP %s\n", id, req, desc);
        return;
    }
    total++;
    if (!ok)
        failures++;
    printf("%s %s %s %s\n", id, req, ok ? "PASS" : "FAIL", desc);
}

static char errbuf[160];

/* Parse the first pipeline of `s` (last_status = 0). */
static ParseResult P(const char *s, Pipeline *pl)
{
    const char *c = s;
    return parse_next_pipeline(&c, 0, pl, errbuf, sizeof errbuf);
}

#define WORD(value) {TOKEN_WORD, (char *)(value), NULL}
#define OPERATOR(value) {value, NULL, NULL}

static int token_failures = 0;
static int token_tests_run = 0;

static void report_failure(const char *name, const char *detail)
{
    fprintf(stderr, "FAIL: %s: %s\n", name, detail);
    ++token_failures;
}

static void expect_tokens(const char *name, const char *line,
                          const Token *expected, size_t expected_count)
{
    TokenList tokens;
    ParseError error;
    ParseStatus status;
    size_t index;

    ++token_tests_run;
    token_list_init(&tokens);
    status = parse_line(line, &tokens, &error);
    if (status != PARSE_STATUS_OK) {
        report_failure(name, error.message);
        token_list_free(&tokens);
        return;
    }
    if (tokens.count != expected_count) {
        report_failure(name, "unexpected token count");
        token_list_free(&tokens);
        return;
    }
    for (index = 0; index < expected_count; ++index) {
        if (tokens.items[index].type != expected[index].type) {
            report_failure(name, "unexpected token type");
            token_list_free(&tokens);
            return;
        }
        if (expected[index].type == TOKEN_WORD &&
            (tokens.items[index].text == NULL ||
             strcmp(tokens.items[index].text, expected[index].text) != 0)) {
            report_failure(name, "unexpected word text");
            token_list_free(&tokens);
            return;
        }
    }
    token_list_free(&tokens);
}

static void expect_error(const char *name, const char *line,
                         const char *expected_message)
{
    TokenList tokens;
    ParseError error;
    ParseStatus status;

    ++token_tests_run;
    token_list_init(&tokens);
    status = parse_line(line, &tokens, &error);
    if (status != PARSE_STATUS_SYNTAX_ERROR) {
        report_failure(name, "expected syntax error status 2");
    } else if (error.status != status) {
        report_failure(name, "error status does not match return value");
    } else if (strcmp(error.message, expected_message) != 0) {
        report_failure(name, error.message);
    } else if (tokens.count != 0) {
        report_failure(name, "failed parse returned partial tokens");
    }
    token_list_free(&tokens);
}

static void expect_expansion_mask(const char *name, const char *line,
                                  size_t token_index,
                                  const unsigned char *expected,
                                  size_t expected_length)
{
    TokenList tokens;
    ParseError error;
    ParseStatus status;

    ++token_tests_run;
    token_list_init(&tokens);
    status = parse_line(line, &tokens, &error);
    if (status != PARSE_STATUS_OK) {
        report_failure(name, error.message);
    } else if (token_index >= tokens.count ||
               tokens.items[token_index].type != TOKEN_WORD) {
        report_failure(name, "word token was not returned");
    } else if (strlen(tokens.items[token_index].text) != expected_length ||
               memcmp(tokens.items[token_index].expansion_mask, expected,
                      expected_length) != 0) {
        report_failure(name, "unexpected expansion context metadata");
    }
    token_list_free(&tokens);
}

static void expect_separate_validation(void)
{
    TokenList tokens;
    ParseError error;
    ParseStatus status;

    ++token_tests_run;
    token_list_init(&tokens);
    status = tokenize("echo hi >", &tokens, &error);
    if (status != PARSE_STATUS_OK) {
        report_failure("separate validation", "tokenizer rejected token sequence");
    } else if (tokens.count != 3) {
        report_failure("separate validation", "tokenizer returned wrong count");
    } else if (validate_syntax(&tokens, &error) !=
                   PARSE_STATUS_SYNTAX_ERROR ||
               strcmp(error.message, "missing file name") != 0) {
        report_failure("separate validation",
                       "validator missed the redirection error");
    } else if (error.status != PARSE_STATUS_SYNTAX_ERROR) {
        report_failure("separate validation", "validator status is inconsistent");
    }
    token_list_free(&tokens);
}

static void expect_large_input(void)
{
    const size_t argument_length = 100000;
    const size_t argument_count = 2000;
    size_t line_length = argument_length + argument_count * 2 - 2;
    char *line = (char *)malloc(line_length + 1);
    TokenList tokens;
    ParseError error;
    ParseStatus status;
    size_t offset;
    size_t index;

    ++token_tests_run;
    if (line == NULL) {
        report_failure("large input", "test allocation failed");
        return;
    }
    memset(line, 'x', argument_length);
    offset = argument_length;
    for (index = 0; index < argument_count - 1; ++index) {
        line[offset++] = ' ';
        line[offset++] = 'a';
    }
    if (offset != line_length) {
        report_failure("large input", "test input length calculation failed");
        free(line);
        return;
    }
    line[line_length] = '\0';

    token_list_init(&tokens);
    status = parse_line(line, &tokens, &error);
    if (status != PARSE_STATUS_OK || tokens.count != argument_count) {
        report_failure("large input", status == PARSE_STATUS_OK
                                          ? "unexpected token count"
                                          : error.message);
    } else if (strlen(tokens.items[0].text) != argument_length) {
        report_failure("large input", "long word was truncated");
    }
    token_list_free(&tokens);
    free(line);
}

static void run_tests(void)
{
    static const Token quoted_unsupported[] = {
        WORD("echo"), WORD("&& ||")
    };
    expect_tokens("quoted unsupported operators", "echo '&& ||'",
                  quoted_unsupported,
                  sizeof(quoted_unsupported) / sizeof(quoted_unsupported[0]));
}

int main(void)
{
    Pipeline pl;
    ParseResult r;
    const char *cur;
    int ok;

    /* UT-01 */
    r = P("echo hello world", &pl);
    ok = r == PARSE_OK && pl.ncmds == 1 && pl.cmds[0].argc == 3 &&
         strcmp(pl.cmds[0].argv[0], "echo") == 0 &&
         strcmp(pl.cmds[0].argv[2], "world") == 0 && pl.cmds[0].argv[3] == NULL;
    report("UT-01", "FR-03", ok, "tokenizes plain words into a NULL-terminated argv");
    if (r == PARSE_OK) pipeline_free(&pl);

    /* UT-02 */
    r = P("echo 'a   b|c;d'", &pl);
    ok = r == PARSE_OK && pl.cmds[0].argc == 2 &&
         strcmp(pl.cmds[0].argv[1], "a   b|c;d") == 0;
    report("UT-02", "FR-03", ok, "single quotes keep spaces and operators literal");
    if (r == PARSE_OK) pipeline_free(&pl);

    /* UT-03 */
    setenv("UT_VAR", "value", 1);
    r = P("echo \"x $UT_VAR y\"", &pl);
    ok = r == PARSE_OK && pl.cmds[0].argc == 2 &&
         strcmp(pl.cmds[0].argv[1], "x value y") == 0;
    report("UT-03", "FR-13", ok, "double quotes expand $VAR and keep spaces");
    if (r == PARSE_OK) pipeline_free(&pl);

    /* UT-04 */
    r = P("echo '$UT_VAR'", &pl);
    ok = r == PARSE_OK && strcmp(pl.cmds[0].argv[1], "$UT_VAR") == 0;
    report("UT-04", "FR-13", ok, "single quotes suppress variable expansion");
    if (r == PARSE_OK) pipeline_free(&pl);

    /* UT-05 */
    r = P("echo a\\ b \\> c", &pl);
    ok = r == PARSE_OK && pl.cmds[0].argc == 4 &&
         strcmp(pl.cmds[0].argv[1], "a b") == 0 &&
         strcmp(pl.cmds[0].argv[2], ">") == 0 && pl.cmds[0].outfile == NULL;
    report("UT-05", "FR-03", ok, "backslash escapes a space and an operator");
    if (r == PARSE_OK) pipeline_free(&pl);

    /* UT-06 */
    r = P("echo hi # this is ignored", &pl);
    ok = r == PARSE_OK && pl.cmds[0].argc == 2;
    report("UT-06", "FR-03", ok, "text after an unquoted # is a comment");
    if (r == PARSE_OK) pipeline_free(&pl);

    /* UT-07 */
    r = P("cat f | grep x | wc -l", &pl);
    ok = r == PARSE_OK && pl.ncmds == 3 &&
         strcmp(pl.cmds[1].argv[0], "grep") == 0 && pl.cmds[2].argc == 2;
    report("UT-07", "FR-18", ok, "pipeline of three commands is split correctly");
    if (r == PARSE_OK) pipeline_free(&pl);

    /* UT-08 */
    r = P("sort < in.txt > out.txt", &pl);
    ok = r == PARSE_OK && pl.cmds[0].argc == 1 &&
         pl.cmds[0].infile && strcmp(pl.cmds[0].infile, "in.txt") == 0 &&
         pl.cmds[0].outfile && strcmp(pl.cmds[0].outfile, "out.txt") == 0 &&
         pl.cmds[0].append == 0;
    report("UT-08", "FR-14", ok, "< and > targets are recorded, not passed as arguments");
    if (r == PARSE_OK) pipeline_free(&pl);

    /* UT-09 */
    r = P("echo x>>log.txt", &pl);
    ok = r == PARSE_OK && pl.cmds[0].outfile &&
         strcmp(pl.cmds[0].outfile, "log.txt") == 0 && pl.cmds[0].append == 1;
    report("UT-09", "FR-15", ok, ">> sets the append flag (no surrounding spaces needed)");
    if (r == PARSE_OK) pipeline_free(&pl);

    /* UT-10 */
    r = P("sleep 5 &", &pl);
    ok = r == PARSE_OK && pl.background == 1 && pl.cmds[0].argc == 2;
    report("UT-10", "FR-20", ok, "trailing & marks the pipeline as background");
    if (r == PARSE_OK) pipeline_free(&pl);

    /* UT-11 */
    cur = "echo one; echo two";
    r = parse_next_pipeline(&cur, 0, &pl, errbuf, sizeof errbuf);
    ok = r == PARSE_OK && strcmp(pl.cmds[0].argv[1], "one") == 0;
    if (r == PARSE_OK) pipeline_free(&pl);
    r = parse_next_pipeline(&cur, 0, &pl, errbuf, sizeof errbuf);
    ok = ok && r == PARSE_OK && strcmp(pl.cmds[0].argv[1], "two") == 0;
    if (r == PARSE_OK) pipeline_free(&pl);
    r = parse_next_pipeline(&cur, 0, &pl, errbuf, sizeof errbuf);
    ok = ok && r == PARSE_END;
    report("UT-11", "FR-19", ok, "; separates pipelines and input ends with PARSE_END");

    /* UT-12 */
    r = P("echo \"unterminated", &pl);
    ok = r == PARSE_ERROR && strstr(errbuf, "unterminated") != NULL;
    report("UT-12", "FR-04", ok, "unterminated double quote is a syntax error");

    r = P("echo 'unterminated", &pl);
    ok = r == PARSE_ERROR && strstr(errbuf, "unterminated single") != NULL;
    report("UT-13", "FR-04", ok, "unterminated single quote is a syntax error");

    /* UT-14 */
    r = P("cat <", &pl);
    ok = r == PARSE_ERROR && strstr(errbuf, "missing file name") != NULL;
    report("UT-14", "FR-04", ok, "redirection without a target is a syntax error");

    /* UT-15 */
    r = P("ls | | wc", &pl);
    ok = r == PARSE_ERROR;
    r = P("| ls", &pl);
    ok = ok && r == PARSE_ERROR;
    r = P("ls |", &pl);
    ok = ok && r == PARSE_ERROR && strstr(errbuf, "missing command") != NULL;
    report("UT-15", "FR-04", ok, "empty pipeline stages ('| ls', 'ls |', 'ls | | wc') are rejected");

    /* UT-16 */
    r = P("echo a && echo b", &pl);
    ok = r == PARSE_ERROR && strstr(errbuf, "&&") != NULL;
    r = P("echo a || echo b", &pl);
    ok = ok && r == PARSE_ERROR && strstr(errbuf, "||") != NULL;
    report("UT-16", "FR-04", ok, "unsupported && and || are reported, not silently mis-parsed");

    /* UT-17 */
    cur = "echo $?";
    r = parse_next_pipeline(&cur, 42, &pl, errbuf, sizeof errbuf);
    ok = r == PARSE_OK && strcmp(pl.cmds[0].argv[1], "42") == 0;
    report("UT-17", "FR-13", ok, "$? expands to the supplied last status");
    if (r == PARSE_OK) pipeline_free(&pl);

    /* UT-18 */
    ok = P("", &pl) == PARSE_END && P("   \t  ", &pl) == PARSE_END &&
         P("# only a comment", &pl) == PARSE_END && P("\n", &pl) == PARSE_END;
    report("UT-18", "FR-01", ok, "blank, whitespace-only and comment-only lines yield PARSE_END");

    /* UT-19 */
    ok = is_valid_name("PATH", 4) && is_valid_name("_x9", 3) &&
         !is_valid_name("9x", 2) && !is_valid_name("", 0) &&
         is_assignment("A=1") && is_assignment("A=") && !is_assignment("=1") &&
         !is_assignment("a-b=1") && !is_assignment("plain");
    report("UT-19", "FR-12", ok, "identifier and NAME=VALUE validation helpers");

    /* UT-20 */
    setenv("HOME", "/home/unit", 1);
    r = P("echo ~ ~/docs a~b", &pl);
    ok = r == PARSE_OK && strcmp(pl.cmds[0].argv[1], "/home/unit") == 0 &&
         strcmp(pl.cmds[0].argv[2], "/home/unit/docs") == 0 &&
         strcmp(pl.cmds[0].argv[3], "a~b") == 0;
    report("UT-20", "FR-13", ok, "leading ~ expands to $HOME; embedded ~ is literal");
    if (r == PARSE_OK) pipeline_free(&pl);

    /* UT-21 */
    unsetenv("UT_UNSET");
    setenv("UT_BRACE", "ab", 1);
    r = P("echo ${UT_BRACE}cd $UT_UNSET end \"$UT_UNSET\"", &pl);
    ok = r == PARSE_OK && pl.cmds[0].argc == 4 &&
         strcmp(pl.cmds[0].argv[1], "abcd") == 0 &&
         strcmp(pl.cmds[0].argv[2], "end") == 0 &&
         strcmp(pl.cmds[0].argv[3], "") == 0;
    report("UT-21", "FR-13", ok, "${NAME} works; unquoted empty expansion is dropped, quoted one kept");
    if (r == PARSE_OK) pipeline_free(&pl);

    /* UT-22 */
    r = P("echo ${bad", &pl);
    ok = r == PARSE_ERROR && strstr(errbuf, "bad substitution") != NULL;
    report("UT-22", "FR-04", ok, "malformed ${...} is reported as a bad substitution");

    /* UT-23 */
    r = P("echo hi > ", &pl);
    ok = r == PARSE_ERROR;
    r = P("> file", &pl);
    ok = ok && r == PARSE_ERROR;
    report("UT-23", "FR-04", ok, "redirection with no command / no target is rejected");

    /* UT-24 */
    r = P("echo a >x >y", &pl);
    ok = r == PARSE_OK && pl.cmds[0].outfile && strcmp(pl.cmds[0].outfile, "y") == 0;
    report("UT-24", "FR-14", ok, "when > is repeated the last target wins");
    if (r == PARSE_OK) pipeline_free(&pl);

    printf("UNIT SUMMARY: %d run, %d passed, %d failed", total, total - failures, failures);
    if (skipped)
        printf(", %d skipped (not implemented yet)", skipped);
    printf("\n");

    static const unsigned char expandable[] = {1U, 1U, 1U, 1U, 1U};
    static const unsigned char literal[] = {0U, 0U, 0U, 0U, 0U};
    static const unsigned char escaped_dollar[] = {0U, 1U, 1U, 1U, 1U};
    static const unsigned char mixed_quotes[] = {
        0U, 0U, 0U, 0U, 0U, 0U, 0U, 1U, 1U, 1U, 1U, 1U
    };
    static const Token normal[] = {
        WORD("echo"), WORD("hello"), WORD("world")
    };
    static const Token whitespace[] = {
        WORD("one"), WORD("two")
    };
    static const Token single_quotes[] = {
        WORD("echo"), WORD("a   b|c;d")
    };
    static const Token single_quote_backslash[] = {
        WORD("echo"), WORD("a\\ b")
    };
    static const Token double_quotes[] = {
        WORD("echo"), WORD("a b|c;d>e&f\"g")
    };
    static const Token escaped[] = {
        WORD("echo"), WORD("a b"), WORD(">"), WORD("c")
    };
    static const Token adjacent_operators[] = {
        WORD("echo"), WORD("x"), OPERATOR(TOKEN_REDIRECT_OUT), WORD("f"),
        OPERATOR(TOKEN_SEMICOLON), WORD("cat"),
        OPERATOR(TOKEN_REDIRECT_IN), WORD("f"),
        OPERATOR(TOKEN_REDIRECT_APPEND), WORD("g"),
        OPERATOR(TOKEN_AMPERSAND), WORD("echo"), WORD("done")
    };
    static const Token quoted_operators[] = {
        WORD("echo"), WORD("|<>>;&")
    };
    static const Token empty_arguments[] = {
        WORD("echo"), WORD(""), WORD(""), WORD("ab"), WORD("")
    };
    static const Token comments[] = {
        WORD("echo"), WORD("x#kept"), WORD("#also-kept")
    };
    static const Token separators_and_comments[] = {
        WORD("echo"), WORD("hi"), OPERATOR(TOKEN_SEMICOLON)
    };
    static const Token literal_expansion[] = {
        WORD("echo"), WORD("$HOME"), WORD("${name}")
    };
    static const Token escaped_hash[] = {
        WORD("echo"), WORD("#not-a-comment")
    };
    static const Token blank[] = { {TOKEN_WORD, NULL, NULL} };

    expect_tokens("normal words", "echo hello world", normal,
                  sizeof(normal) / sizeof(normal[0]));
    expect_tokens("whitespace separators", " \t one  two \n", whitespace,
                  sizeof(whitespace) / sizeof(whitespace[0]));
    expect_tokens("single quotes preserve literal text",
                  "echo 'a   b|c;d'", single_quotes,
                  sizeof(single_quotes) / sizeof(single_quotes[0]));
    expect_tokens("single quotes keep backslashes literal",
                  "echo 'a\\ b'", single_quote_backslash,
                  sizeof(single_quote_backslash) /
                      sizeof(single_quote_backslash[0]));
    expect_tokens("double quotes and escaping",
                  "echo \"a b|c;d>e&f\\\"g\"", double_quotes,
                  sizeof(double_quotes) / sizeof(double_quotes[0]));
    expect_tokens("escaped space and operator", "echo a\\ b \\> c", escaped,
                  sizeof(escaped) / sizeof(escaped[0]));
    expect_tokens("adjacent operators",
                  "echo x>f;cat<f>>g&echo done", adjacent_operators,
                  sizeof(adjacent_operators) / sizeof(adjacent_operators[0]));
    expect_tokens("quoted operators", "echo '|<>>;&'", quoted_operators,
                  sizeof(quoted_operators) / sizeof(quoted_operators[0]));
    expect_tokens("empty and concatenated quoted arguments",
                  "echo \"\" '' a\"b\" ''", empty_arguments,
                  sizeof(empty_arguments) / sizeof(empty_arguments[0]));
    expect_tokens("comments and hashes inside words",
                  "echo x#kept ''#also-kept # ignored", comments,
                  sizeof(comments) / sizeof(comments[0]));
    expect_tokens("comment follows a separator", "echo hi;# ignored",
                  separators_and_comments,
                  sizeof(separators_and_comments) /
                      sizeof(separators_and_comments[0]));
    expect_tokens("escaped hash", "echo \\#not-a-comment", escaped_hash,
                  sizeof(escaped_hash) / sizeof(escaped_hash[0]));
    expect_tokens("expansion remains literal", "echo '$HOME' \"${name}\"",
                  literal_expansion,
                  sizeof(literal_expansion) / sizeof(literal_expansion[0]));
    expect_expansion_mask("unquoted expansion context",
                          "echo $HOME \"$HOME\" '$HOME' \\$HOME", 1,
                          expandable, sizeof(expandable));
    expect_expansion_mask("double-quoted expansion context",
                          "echo $HOME \"$HOME\" '$HOME' \\$HOME", 2,
                          expandable, sizeof(expandable));
    expect_expansion_mask("single-quoted literal context",
                          "echo $HOME \"$HOME\" '$HOME' \\$HOME", 3,
                          literal, sizeof(literal));
    expect_expansion_mask("escaped dollar context",
                          "echo $HOME \"$HOME\" '$HOME' \\$HOME", 4,
                          escaped_dollar, sizeof(escaped_dollar));
    expect_expansion_mask("mixed quote segments",
                          "echo 'literal'$HOME", 1, mixed_quotes,
                          sizeof(mixed_quotes));
    expect_tokens("empty input", " \t\r\n", blank, 0);
    expect_tokens("comment-only input", "# ignored", blank, 0);
    expect_separate_validation();
    run_tests();

    expect_error("unterminated double quote", "echo \"unterminated",
                 "unterminated double quote");
    expect_error("syntax error discards preceding commands",
                 "echo before; echo \"oops; echo after",
                 "unterminated double quote");
    expect_error("unterminated single quote", "echo 'unterminated",
                 "unterminated single quote");
    expect_error("leading pipe", "| ls", "empty pipeline stage");
    expect_error("trailing pipe", "ls |", "empty pipeline stage");
    expect_error("doubled pipe stage", "ls | | wc", "empty pipeline stage");
    expect_error("doubled pipe", "ls ||| wc", "|| is not supported");
    expect_error("missing input target", "cat <", "missing file name");
    expect_error("missing target before separator", "echo hi > ;",
                 "missing file name");
    expect_error("redirection without command", "> lonely.txt",
                 "redirection without a command");
    expect_error("redirection in a pipeline without command", "> f | cat",
                 "redirection without a command");
    expect_error("unsupported and", "echo a && echo b",
                 "&& is not supported");
    expect_error("unsupported or", "false || echo b",
                 "|| is not supported");
    expect_error("malformed substitution", "echo ${bad", "bad substitution");
    expect_error("malformed substitution in double quotes",
                 "echo \"${bad\" # }", "bad substitution");
    expect_error("empty redirection target", "cat < \"\"", "missing file name");
    expect_error("trailing escape", "echo trailing\\", "trailing escape");

    expect_large_input();

    if (token_failures != 0) {
        fprintf(stderr, "%d of %d tokenizer tests failed\n",
                token_failures, token_tests_run);
    } else {
        printf("All %d tokenizer tests passed\n", token_tests_run);
    }
    return failures || token_failures ? EXIT_FAILURE : EXIT_SUCCESS;
}
