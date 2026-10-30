/*
 * shell.c - Shell lifecycle: initialisation, signal setup, read-eval loop.
 * Owner: Member 1 (Shell core architecture)
 */
#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200809L
#endif
#ifndef _DEFAULT_SOURCE
#define _DEFAULT_SOURCE
#endif

#include "shell.h"

#include <errno.h>
#include <limits.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "executor.h"
#include "parser.h"
#include "utils.h"

volatile sig_atomic_t g_sigint_flag = 0;


void shell_init(Shell *sh)
{
    memset(sh, 0, sizeof *sh);
    sh->running = 1;
    sh->next_job_id = 1;
    sh->interactive = isatty(STDIN_FILENO);
}

void shell_cleanup(Shell *sh)
{
    int i;
    for (i = 0; i < sh->njobs; i++)
        free(sh->jobs[i].text);
    sh->njobs = 0;
}

void shell_setup_signals(const Shell *sh)
{
    (void)sh;       /* Ctrl+C handling is added by story FR-21 */
}

int shell_execute_line(Shell *sh, const char *line)
{
    const char *cursor = line;

    while (sh->running) {
        Pipeline pl;
        char err[160];
        ParseResult r = parse_next_pipeline(&cursor, sh->last_status,
                                            &pl, err, sizeof err);
        if (r == PARSE_END)
            break;
        if (r == PARSE_ERROR) {
            shell_error("%s", err);
            sh->last_status = 2;
            break;
        }
        sh->last_status = execute_pipeline(sh, &pl);
        pipeline_free(&pl);
    }
    return sh->last_status;
}

static void print_prompt(void)
{
    char cwd[PATH_MAX];
    if (getcwd(cwd, sizeof cwd))
        fprintf(stderr, SHELL_NAME ":%s$ ", cwd);
    else
        fprintf(stderr, SHELL_NAME "$ ");
    fflush(stderr);
}

int shell_run_stream(Shell *sh, FILE *in)
{
    char *line = NULL;
    size_t cap = 0;

    while (sh->running) {
        ssize_t n;

        jobs_reap(sh);


        if (sh->interactive)
            print_prompt();

        errno = 0;
        n = getline(&line, &cap, in);
        if (n < 0) {
            if (sh->interactive)
                fputs("exit\n", stderr);     /* Ctrl+D */
            break;
        }
        g_sigint_flag = 0;
        shell_execute_line(sh, line);
    }
    free(line);
    return sh->running ? sh->last_status : sh->exit_code;
}
