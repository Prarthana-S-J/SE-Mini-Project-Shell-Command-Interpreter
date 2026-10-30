
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


static int redirect_input(const Command *c)
{
    int fd;

    if (c->infile == NULL)
        return 0;

    fd = open(c->infile, O_RDONLY);
    if (fd < 0) {
        shell_error("%s: %s", c->infile, strerror(errno));
        return -1;
    }

    if (dup2(fd, STDIN_FILENO) < 0) {
        int saved_errno = errno;
        if (fd != STDIN_FILENO)
            close(fd);
        shell_error("%s: %s", c->infile, strerror(saved_errno));
        return -1;
    }

    if (fd != STDIN_FILENO)
        close(fd);
    return 0;
}


static int redirect_output(const Command *c)
{
    int fd;

    if (c->outfile == NULL)
        return 0;

    int flags = O_WRONLY | O_CREAT;

    if (c->append)
        flags |= O_APPEND;
    else
        flags |= O_TRUNC;

    fd = open(c->outfile, flags, 0644);
    if (fd < 0) {
        shell_error("%s: %s", c->outfile, strerror(errno));
        return -1;
    }

    if (dup2(fd, STDOUT_FILENO) < 0) {
        int saved_errno = errno;
        if (fd != STDOUT_FILENO)
            close(fd);
        shell_error("%s: %s", c->outfile, strerror(saved_errno));
        return -1;
    }

    if (fd != STDOUT_FILENO)
        close(fd);
    return 0;
}


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
        if (in_fd != STDIN_FILENO)
            close(in_fd);
    }

    if (out_fd >= 0) {
        if (dup2(out_fd, STDOUT_FILENO) == -1) {
            shell_error("stdout redirection: %s", strerror(errno));
            _exit(126);
        }
        if (out_fd != STDOUT_FILENO)
            close(out_fd);
    }

    if (redirect_input(c) < 0)
        _exit(1);

    if (redirect_output(c) < 0)
        _exit(1);

    if (is_builtin(c->argv[0])) {
        int builtin_status = run_builtin(sh, c->argc, c->argv);
        fflush(NULL);
        _exit(builtin_status);
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


/* ---- Parent side ------------------------------------------------------- */

static int wait_foreground(const pid_t *pids, int n)
{
    int i, status = 0, last_status = 0;

    for (i = 0; i < n; i++) {
        while (waitpid(pids[i], &status, 0) < 0) {
            if (errno == EINTR)
                continue;
            status = 0;
            break;
        }
        if (i == n - 1)
            last_status = status;
    }
    if (WIFSIGNALED(last_status) && WTERMSIG(last_status) != SIGPIPE)
        fprintf(stderr, "%s\n", strsignal(WTERMSIG(last_status)));
    if (WIFEXITED(last_status))
        return WEXITSTATUS(last_status);
    if (WIFSIGNALED(last_status))
        return 128 + WTERMSIG(last_status);
    return 1;
}



/* ---- Environment assignments ----------------------------------------- */

/* A command consisting entirely of NAME=VALUE words updates the shell
   environment instead of trying to execute the first word as a program. */
static int all_assignments(const Command *c)
{
    int i;

    if (c->argc == 0 || c->infile != NULL || c->outfile != NULL)
        return 0;

    for (i = 0; i < c->argc; i++) {
        if (!is_assignment(c->argv[i]))
            return 0;
    }

    return 1;
}

static int run_assignments(const Command *c)
{
    int i;
    int status = 0;

    for (i = 0; i < c->argc; i++) {
        const char *equals = strchr(c->argv[i], '=');
        size_t name_len = (size_t)(equals - c->argv[i]);
        char *name = xmalloc(name_len + 1);

        memcpy(name, c->argv[i], name_len);
        name[name_len] = '\0';

        if (setenv(name, equals + 1, 1) != 0) {
            shell_error("cannot set variable %s: %s",
                        name, strerror(errno));
            status = 1;
        }

        free(name);
    }

    return status;
}


int execute_pipeline(Shell *sh, const Pipeline *pl)
{
    int n = pl->ncmds;
    int i, prev_read = -1, forked = 0, status;
    pid_t *pids;

    if (n <= 0)
        return 0;

    if (n == 1 && !pl->background &&
        all_assignments(&pl->cmds[0])) {
        return run_assignments(&pl->cmds[0]);
    }

    if (n == 1 && !pl->background &&
        is_builtin(pl->cmds[0].argv[0])) {
        const Command *c = &pl->cmds[0];
        int saved_out = -1;

        if (c->outfile != NULL) {
            saved_out = dup(STDOUT_FILENO);
            if (saved_out < 0) {
                shell_error("dup: %s", strerror(errno));
                return 1;
            }

            if (redirect_output(c) < 0) {
                (void)dup2(saved_out, STDOUT_FILENO);
                close(saved_out);
                return 1;
            }
        }

        status = run_builtin(sh, c->argc, c->argv);
        fflush(stdout);

        if (saved_out >= 0) {
            if (dup2(saved_out, STDOUT_FILENO) < 0) {
                shell_error("dup2: %s", strerror(errno));
                status = 1;
            }
            close(saved_out);
        }

        return status;
    }

    pids = xmalloc((size_t)n * sizeof(pid_t));
    fflush(NULL);

    for (i = 0; i < n; i++) {
        int fd[2] = { -1, -1 };
        pid_t pid;

        /* Create a pipe for every command except the last. */
        if (i < n - 1 && pipe(fd) < 0) {
            shell_error("pipe: %s", strerror(errno));
            break;
        }

        pid = fork();

        if (pid < 0) {
            shell_error("fork: %s", strerror(errno));

            if (fd[0] >= 0)
                close(fd[0]);
            if (fd[1] >= 0)
                close(fd[1]);

            break;
        }

        if (pid == 0) {
            if (fd[0] >= 0)
                close(fd[0]);

            exec_child(sh, &pl->cmds[i], prev_read, fd[1],
                       pl->background, i == 0);
        }

        pids[forked++] = pid;

        /* Parent no longer needs the previous pipe's read end. */
        if (prev_read >= 0)
            close(prev_read);

        /* Parent must close the write end so readers can see EOF. */
        if (fd[1] >= 0)
            close(fd[1]);

        prev_read = fd[0];
    }

    if (prev_read >= 0)
        close(prev_read);

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