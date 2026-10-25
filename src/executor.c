
/*
 * executor.c - fork/exec, redirection, pipelines, background jobs.
 * Owner: Member 1 (process creation, wait, exit status)
 *        Member 3 (redirection, pipes, background execution, job reaping)
 */
#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200809L
#endif
#ifndef _DEFAULT_SOURCE
#define _DEFAULT_SOURCE
#endif

#include "executor.h"

#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

#include "builtins.h"
#include "utils.h"

static void exec_child(Shell *sh, const Command *c, int in_fd, int out_fd,
                       int background, int first)
{
    (void)background;
    (void)first;
    (void)sh;

    if (in_fd >= 0) {
        if (dup2(in_fd, STDIN_FILENO) == -1) {
            shell_error("stdin redirection: %s", strerror(errno));
            _exit(126);
        }
        close(in_fd);
    }

    if (out_fd >= 0) {
        if (dup2(out_fd, STDOUT_FILENO) == -1) {
            shell_error("stdout redirection: %s", strerror(errno));
            _exit(126);
        }
        close(out_fd);
    }

    execvp(c->argv[0], c->argv);

    if (errno == ENOENT) {
        if (strchr(c->argv[0], '/'))
            shell_error("%s: No such file or directory", c->argv[0]);
        else
            shell_error("%s: command not found", c->argv[0]);
        _exit(127);
    }

    shell_error("%s: %s", c->argv[0], strerror(errno));
    _exit(126);
}

static int wait_foreground(const pid_t *pids, int n)
{
    int i, status = 0, last_status = 0;
    int wait_failed = 0;

    for (i = 0; i < n; i++) {
        pid_t result;

        do {
            result = waitpid(pids[i], &status, 0);
        } while (result < 0 && errno == EINTR);

        if (result < 0) {
            shell_error("waitpid: %s", strerror(errno));
            wait_failed = 1;
            continue;
        }

        if (i == n - 1)
            last_status = status;
    }

    if (wait_failed)
        return 1;

    if (WIFSIGNALED(last_status) && WTERMSIG(last_status) != SIGPIPE)
        fprintf(stderr, "%s\n", strsignal(WTERMSIG(last_status)));

    if (WIFEXITED(last_status))
        return WEXITSTATUS(last_status);

    if (WIFSIGNALED(last_status))
        return 128 + WTERMSIG(last_status);

    return 1;
}

int execute_pipeline(Shell *sh, const Pipeline *pl)
{
    int n = pl->ncmds, i, prev_read = -1, forked = 0, status;
    pid_t *pids;

    pids = xmalloc((size_t)n * sizeof(pid_t));
    fflush(NULL);

    for (i = 0; i < n; i++) {
        int fd[2] = { -1, -1 };
        pid_t pid;

        pid = fork();
        if (pid < 0) {
            shell_error("fork: %s", strerror(errno));
            if (fd[0] >= 0) {
                close(fd[0]);
                close(fd[1]);
            }
            break;
        }

        if (pid == 0) {
            exec_child(sh, &pl->cmds[i], prev_read, fd[1],
                       pl->background, i == 0);
        }

        pids[forked++] = pid;
    }

    if (forked < n) {
        for (i = 0; i < forked; i++)
            waitpid(pids[i], NULL, 0);
        free(pids);
        return 1;
    }

    status = wait_foreground(pids, n);
    free(pids);
    return status;
}
