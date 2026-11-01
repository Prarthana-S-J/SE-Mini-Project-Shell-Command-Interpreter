/*
 * builtins.c - cd and pwd built-in commands.
 * Owner: Member 2 (Built-in commands, environment handling)
 */
#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200809L
#endif
#ifndef _DEFAULT_SOURCE
#define _DEFAULT_SOURCE
#endif

#include "builtins.h"

#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "utils.h"
extern char **environ;



static int bi_cd(int argc, char **argv)
{
    const char *target;
    char oldcwd[PATH_MAX];
    char newcwd[PATH_MAX];
    int print_dir = 0;

    if (argc > 2) {
        shell_error("cd: too many arguments");
        return 1;
    }

    if (argc == 1) {
        target = getenv("HOME");
        if (target == NULL || *target == '\0') {
            shell_error("cd: HOME not set");
            return 1;
        }
    } else if (strcmp(argv[1], "-") == 0) {
        target = getenv("OLDPWD");
        if (target == NULL || *target == '\0') {
            shell_error("cd: OLDPWD not set");
            return 1;
        }
        print_dir = 1;
    } else {
        target = argv[1];
    }

    if (getcwd(oldcwd, sizeof oldcwd) == NULL)
        oldcwd[0] = '\0';

    if (chdir(target) != 0) {
        shell_error("cd: %s: %s", target, strerror(errno));
        return 1;
    }

    if (oldcwd[0] != '\0' && setenv("OLDPWD", oldcwd, 1) != 0) {
        shell_error("cd: cannot update OLDPWD: %s", strerror(errno));
        return 1;
    }

    if (getcwd(newcwd, sizeof newcwd) != NULL) {
        if (setenv("PWD", newcwd, 1) != 0) {
            shell_error("cd: cannot update PWD: %s", strerror(errno));
            return 1;
        }

        if (print_dir)
            printf("%s\n", newcwd);
    }

    return 0;
}

static int bi_pwd(void)
{
    char cwd[PATH_MAX];

    if (getcwd(cwd, sizeof cwd) == NULL) {
        shell_error("pwd: %s", strerror(errno));
        return 1;
    }

    printf("%s\n", cwd);
    return 0;
}

static int bi_help(void)
{
    printf("Built-in commands:\n");
    printf("  cd [dir]       Change the current directory\n");
    printf("  pwd            Print the current working directory\n");
    printf("  exit [status]  Exit the shell with the specified status\n");
    printf("  help           Display this help message\n");
    printf("  export NAME=VALUE  Set or export an environment variable\n");
    printf("  unset NAME     Remove an environment variable\n");
    printf("  env            Display environment variables\n");
    printf("\n");
    printf("Operators:\n");
    printf("  ;              Run commands in sequence\n");
    printf("  |              Connect commands using a pipeline\n");
    printf("  <              Redirect standard input\n");
    printf("  >              Redirect standard output (overwrite)\n");
    printf("  >>             Redirect standard output (append)\n");

    return 0;
}
static int bi_env(void)
{
    char **entry;

    for (entry = environ; *entry != NULL; entry++) {
        puts(*entry);
    }

    return 0;
}

static int bi_export(int argc, char **argv)
{
    char *equals;
    size_t name_len;

    if (argc != 2) {
        shell_error("export: usage: export NAME=VALUE");
        return 1;
    }

    equals = strchr(argv[1], '=');
    if (equals == NULL) {
        shell_error("export: expected NAME=VALUE");
        return 1;
    }

    name_len = (size_t)(equals - argv[1]);

    if (!is_valid_name(argv[1], name_len)) {
        shell_error("export: not a valid identifier");
        return 1;
    }

    *equals = '\0';

    if (setenv(argv[1], equals + 1, 1) != 0) {
        shell_error("export: cannot set variable");
        *equals = '=';
        return 1;
    }

    *equals = '=';
    return 0;
}

static int bi_unset(int argc, char **argv)
{
    if (argc != 2) {
        shell_error("unset: usage: unset NAME");
        return 1;
    }

    if (!is_valid_name(argv[1], strlen(argv[1]))) {
        shell_error("unset: not a valid identifier");
        return 1;
    }

    if (unsetenv(argv[1]) != 0) {
        shell_error("unset: cannot remove variable");
        return 1;
    }

    return 0;
}
static int bi_exit(Shell *sh, int argc, char **argv)
{
    char *end;
    long code;

    if (argc > 2) {
        shell_error("exit: too many arguments");
        return 1;
    }

    if (argc == 1) {
        sh->exit_code = sh->last_status;
    } else {
        errno = 0;
        code = strtol(argv[1], &end, 10);

        if (argv[1][0] == '\0' || *end != '\0' ||
            errno == ERANGE || code < 0 || code > 255) {
            shell_error("exit: numeric argument required");
            sh->exit_code = 2;
            sh->running = 0;
            return 2;
        }

        sh->exit_code = (int)code;
    }

    sh->running = 0;
    return 0;
}

int is_builtin(const char *name)
{
    return strcmp(name, "cd") == 0 ||
           strcmp(name, "pwd") == 0 ||
	   strcmp(name, "exit") == 0 ||
	   strcmp(name, "help") == 0 ||
            strcmp(name, "export") == 0 ||
           strcmp(name, "unset") == 0 ||
           strcmp(name, "env") == 0;

}

int run_builtin(Shell *sh, int argc, char **argv)
{
    (void)sh;

    if (argc == 0 || argv == NULL || argv[0] == NULL)
        return 1;

    if (strcmp(argv[0], "cd") == 0)
        return bi_cd(argc, argv);

    if (strcmp(argv[0], "pwd") == 0)
        return bi_pwd();

    if (strcmp(argv[0], "help") == 0)
        return bi_help();

    if (strcmp(argv[0], "exit") == 0)
        return bi_exit(sh, argc, argv);
    if (strcmp(argv[0], "export") == 0)
        return bi_export(argc, argv);

    if (strcmp(argv[0], "unset") == 0)
        return bi_unset(argc, argv);

    if (strcmp(argv[0], "env") == 0)
        return bi_env();

    return 127;
}
