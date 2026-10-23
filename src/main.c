/*
 * main.c - Program entry point and command-line options.
 * Owner: Member 1 (Shell core architecture)
 *
 * Usage:  mysh                 interactive shell (or reads commands from stdin)
 *         mysh -c "command"    run one command string and exit
 *         mysh script.sh       run commands from a file
 */
#include <stdio.h>

#include "shell.h"

int main(void)
{
    Shell sh;
    int rc;

    shell_init(&sh);
    shell_setup_signals(&sh);
    rc = shell_run_stream(&sh, stdin);
    shell_cleanup(&sh);
    return rc;
}
