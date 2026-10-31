/*
 * main.c - Program entry point and command-line options.
 * Owner: Member 1 (Shell core architecture)
 *
 * Usage:  mysh                 interactive shell (or reads commands from stdin)
 *         mysh -c "command"    run one command string and exit
 *         mysh script.sh       run commands from a file
 */
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>

#include "shell.h"
#include "utils.h"

static void usage(FILE *out)
{
    fprintf(out, "Usage: %s [-c command | script_file]\n"
                 "       %s -h | --help | --version\n", SHELL_NAME, SHELL_NAME);
}

int main(int argc, char **argv)
{
    Shell sh;
    int rc;

    if (argc >= 2 && (strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0)) {
        usage(stdout);
        return 0;
    }
    if (argc >= 2 && strcmp(argv[1], "--version") == 0) {
        printf("%s %s\n", SHELL_NAME, SHELL_VERSION);
        return 0;
    }

    shell_init(&sh);

    if (argc >= 2 && strcmp(argv[1], "-c") == 0) {
        if (argc < 3) {
            fprintf(stderr, "%s: -c requires an argument\n", SHELL_NAME);
            usage(stderr);
            return 2;
        }
        sh.interactive = 0;
        shell_execute_line(&sh, argv[2]);
        rc = sh.running ? sh.last_status : sh.exit_code;
    } else if (argc >= 2) {
        FILE *f = fopen(argv[1], "r");
        if (!f) {
            shell_error("%s: cannot open script file", argv[1]);
            return 127;
        }
        if (fcntl(fileno(f), F_SETFD, FD_CLOEXEC) == -1) {
             shell_error("%s: cannot set close-on-exec", argv[1]);
             fclose(f);
             shell_cleanup(&sh);
             return 1;
        }
        sh.interactive = 0;
        rc = shell_run_stream(&sh, f);
        fclose(f);
    } else {
        shell_setup_signals(&sh);
        rc = shell_run_stream(&sh, stdin);
    }

    shell_cleanup(&sh);
    return rc;
}
