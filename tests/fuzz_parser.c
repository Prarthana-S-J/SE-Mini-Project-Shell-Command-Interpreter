/*
 * fuzz_parser.c - Randomised robustness test for the parser (security validation).
 * Owner: Member 4 (Testing) / Member 2 (Parser)
 *
 * Generates pseudo-random command lines from a vocabulary of shell metacharacters,
 * quotes, expansions and arbitrary bytes, feeds them to parse_next_pipeline() and
 * checks structural invariants. Build with AddressSanitizer + UBSan (make fuzz) so any
 * memory error aborts the run.   Output: one result line "<ID> <REQ> PASS|FAIL <text>".
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "parser.h"
#include "utils.h"

#define ITERATIONS 200000UL

static unsigned long long state = 0x9E3779B97F4A7C15ULL;
static unsigned long rnd(void)            /* xorshift64*, deterministic */
{
    state ^= state >> 12; state ^= state << 25; state ^= state >> 27;
    return (unsigned long)((state * 0x2545F4914F6CDD1DULL) >> 33);
}

static const char *vocab[] = {
    "echo", "a", "b", "x=1", "|", "||", "<", ">", ">>", ";", "&", "&&", "'", "\"", "\\",
    "$", "${", "}", "$?", "$$", "$HOME", "${HOME}", "~", "~/x", "#", " ", " ", " ", "\t", "\n",
    "$(", "`", "*", "?", "[", "=", "-", "0", "{", "(", ")", "!", "\\\n", "\"$a\"", "'$a'"
};
#define NV (sizeof vocab / sizeof vocab[0])

int main(void)
{
    unsigned long i, ok_parse = 0, errors = 0, ends = 0, violations = 0;
    char line[1024], err[160];

    setenv("HOME", "/home/fuzz", 1);
    for (i = 0; i < ITERATIONS; i++) {
        size_t len = 0, pieces = rnd() % 40, p;
        const char *cur;
        int guard = 0;

        line[0] = '\0';
        for (p = 0; p < pieces && len < sizeof line - 8; p++) {
            if (rnd() % 12 == 0) {                 /* arbitrary non-NUL byte */
                line[len++] = (char)(1 + rnd() % 255);
                line[len] = '\0';
            } else {
                const char *w = vocab[rnd() % NV];
                size_t wl = strlen(w);
                memcpy(line + len, w, wl + 1);
                len += wl;
            }
        }
        cur = line;
        while (guard++ < 200) {
            Pipeline pl;
            ParseResult r = parse_next_pipeline(&cur, (int)(rnd() % 256), &pl, err, sizeof err);
            if (r == PARSE_END) { ends++; break; }
            if (r == PARSE_ERROR) {
                errors++;
                if (err[0] == '\0' || *cur != '\0') violations++;   /* message + input discarded */
                break;
            }
            ok_parse++;
            if (pl.ncmds < 1 || pl.text == NULL) violations++;
            for (int c = 0; c < pl.ncmds; c++) {
                const Command *cmd = &pl.cmds[c];
                if (cmd->argc < 1 || cmd->argv[cmd->argc] != NULL) violations++;
                for (int k = 0; k < cmd->argc; k++)
                    if (cmd->argv[k] == NULL) violations++;
            }
            pipeline_free(&pl);
        }
    }
    printf("SC-12 SR-06 %s parser fuzz: %lu random inputs (%lu pipelines parsed, %lu syntax errors, "
           "%lu empty), %lu invariant violations, sanitizer reports: none (run aborts on any)\n",
           violations == 0 ? "PASS" : "FAIL", ITERATIONS, ok_parse, errors, ends, violations);
    return violations ? 1 : 0;
}
