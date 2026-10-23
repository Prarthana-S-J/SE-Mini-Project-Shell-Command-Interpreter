#!/usr/bin/env python3
"""fuzz_shell.py - process-level robustness test (security validation, Member 4).

Runs the *real* shell binary (normally the ASan/UBSan build) on N random command lines made
only from harmless words (echo/true/false/x/y), operators, quotes, variables and file names f1..f3
inside a throw-away directory.  Pass criteria: the shell is never killed by a signal, never hangs
(5 s timeout) and prints no sanitizer report.   Output: "SC-13 SR-06 PASS|FAIL ..."
"""
import os, random, subprocess, sys, tempfile

MYSH = os.environ.get("MYSH", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mysh"))
N = int(os.environ.get("FUZZ_N", "600"))
VOCAB = ["echo", "true", "false", "x", "y", "f1", "f2", "f3", "|", "|", "<", ">", ">>", ";", "&", "&&", "||",
         "'", '"', "\\", "$", "${", "}", "$?", "$$", "$HOME", "~", "#", "a b", "=", "x=1", "export", "unset", "env",
         "pwd", "help", "-n", "\t", "\n", "'q'", '"$HOME"', "\\;", ">f1", "<f1", ">>f2", "2"]
rng = random.Random(20261003)
bad = []
workdir = tempfile.mkdtemp(prefix="mysh-fuzz-")
env = dict(os.environ, HOME=workdir, ASAN_OPTIONS="detect_leaks=1:abort_on_error=0", UBSAN_OPTIONS="print_stacktrace=1")
for i in range(N):
    line = " ".join(rng.choice(VOCAB) for _ in range(rng.randint(1, 14)))
    try:
        p = subprocess.run([MYSH, "-c", line], cwd=workdir, env=env, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, errors="replace", timeout=5)
    except subprocess.TimeoutExpired:
        bad.append((line, "timeout")); continue
    err = p.stderr
    if p.returncode < 0:
        bad.append((line, f"killed by signal {-p.returncode}"))
    elif "Sanitizer" in err or "runtime error" in err:
        bad.append((line, "sanitizer report"))
ok = not bad
print(f"SC-13 SR-06 {'PASS' if ok else 'FAIL'} process-level fuzz: {N} random command lines run through the real shell "
      f"(sanitizer build if MYSH is the ASan binary), {len(bad)} crashes/hangs/sanitizer reports")
for line, why in bad[:5]:
    print(f"      -> {why}: {line!r}")
sys.exit(0 if ok else 1)
