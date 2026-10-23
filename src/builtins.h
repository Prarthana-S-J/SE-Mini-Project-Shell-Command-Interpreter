/*
 * builtins.h - Built-in commands executed inside the shell process.
 * Owner: Member 2 (Built-in commands, environment handling)
 */
#ifndef BUILTINS_H
#define BUILTINS_H

#include "shell.h"

/* Returns 1 if `name` is a built-in command. */
int is_builtin(const char *name);

/* Run built-in argv[0]; returns its exit status. */
int run_builtin(Shell *sh, int argc, char **argv);

#endif /* BUILTINS_H */
