/*
 * shell.h - Shell state and lifecycle.
 * Owner: Member 1 (Shell core architecture)
 */
#ifndef SHELL_H
#define SHELL_H

#include <signal.h>
#include <stdio.h>
#include <sys/types.h>

#define MAX_JOBS 64

typedef struct {
    int   id;             /* job number shown as [id]                   */
    pid_t pid;            /* PID of the last process in the pipeline    */
    char *text;           /* command text for the "Done" notification   */
} Job;

typedef struct {
    int  last_status;     /* value of $?                                */
    int  running;         /* main loop continues while non-zero         */
    int  exit_code;       /* process exit code when the shell quits     */
    int  interactive;     /* stdin is a terminal                        */
    int  next_job_id;
    int  njobs;
    Job  jobs[MAX_JOBS];  /* background jobs still to be reported       */
} Shell;

/* Set to 1 by the SIGINT handler; cleared by the main loop. */
extern volatile sig_atomic_t g_sigint_flag;

void shell_init(Shell *sh);
void shell_cleanup(Shell *sh);

/* Install signal dispositions for the shell process (interactive mode). */
void shell_setup_signals(const Shell *sh);

/* Parse and execute every pipeline found in `line`. Returns last status. */
int  shell_execute_line(Shell *sh, const char *line);

/* Read-eval loop over a stream (terminal, pipe or script file). */
int  shell_run_stream(Shell *sh, FILE *in);

#endif /* SHELL_H */
