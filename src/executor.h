/*
 * executor.h - Process creation, redirection, pipes, background jobs.
 * Owner: Member 1 (fork/exec/wait) and Member 3 (redirection, pipes, jobs)
 */
#ifndef EXECUTOR_H
#define EXECUTOR_H

#include "parser.h"
#include "shell.h"

/* Execute a parsed pipeline. Returns its exit status (also the value of $?). */
int  execute_pipeline(Shell *sh, const Pipeline *pl);

/* Collect finished background jobs (non-blocking) and report them. */
void jobs_reap(Shell *sh);

#endif /* EXECUTOR_H */
