/*
 * test_parser.c - Unit tests for the parser and utility helpers.
 * Owner: Member 4 (Testing)
 *
 * Build/run:  make unit-test
 * Output line format:  <ID> <REQ> PASS|FAIL <description>
 */
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
    return failures ? 1 : 0;
}
