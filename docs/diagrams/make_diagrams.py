#!/usr/bin/env python3
"""Generate all project diagrams (PNG) from source. Requires graphviz `dot` and matplotlib.
Run:  python3 docs/diagrams/make_diagrams.py
Every diagram documents behaviour that exists in src/ (see docs/DESIGN.md)."""
import os, subprocess
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = 'fontname="Helvetica"'

def dot(name, src):
    path = os.path.join(HERE, name + ".dot")
    with open(path, "w") as f:
        f.write(src)
    subprocess.check_call(["dot", "-Tpng", "-Gdpi=130", path, "-o", os.path.join(HERE, name + ".png")])

# 1. System architecture -------------------------------------------------------
dot("01_architecture", f'''digraph G {{
 rankdir=TB; nodesep=0.35; ranksep=0.5; node [shape=box, style="rounded,filled", {FONT}, fontsize=11]; edge [{FONT}, fontsize=9];
 user [label="User (terminal / script file / -c string)", fillcolor="#e8f0fe"];
 subgraph cluster_p {{ label="mysh process"; {FONT}; style="rounded"; color="#888888";
  main [label="main.c\\nentry point, option handling", fillcolor="#fff2cc"];
  shell [label="shell.c\\nlifecycle, prompt, read loop,\\nsignal setup, $? state", fillcolor="#fff2cc"];
  parser [label="parser.c\\ntokenizer, quoting, expansion,\\npipeline builder", fillcolor="#d9ead3"];
  exec [label="executor.c\\nfork/exec, pipes, redirection,\\nwait, background jobs", fillcolor="#f4cccc"];
  bi [label="builtins.c\\ncd pwd exit help\\nexport unset env", fillcolor="#d9ead3"];
  utils [label="utils.c\\nmemory, errors, StrBuf, name checks", fillcolor="#eeeeee"];
 }}
 os [label="POSIX kernel interface\\nfork  execvp  pipe  dup2  open  waitpid  sigaction  chdir  getcwd  setenv", fillcolor="#e8f0fe"];
 user -> main [label="keystrokes / args"]; main -> shell; shell -> parser [label="line -> Pipeline"];
 shell -> exec [label="Pipeline"]; exec -> bi [label="built-in?"];
 parser -> utils [style=dashed]; exec -> utils [style=dashed]; bi -> utils [style=dashed]; shell -> utils [style=dashed];
 exec -> os; bi -> os; shell -> os [label="signals"];
 os -> user [label="program output", style=dotted, constraint=false];
}}''')

# 2. Component / module diagram -------------------------------------------------
dot("02_components", f'''digraph G {{
 rankdir=LR; node [shape=component, style=filled, fillcolor="#fff2cc", {FONT}, fontsize=11]; edge [{FONT}, fontsize=9];
 main [label="main.c"]; shell [label="shell.c / shell.h\\nShell, Job structs"]; parser [label="parser.c / parser.h\\nCommand, Pipeline structs"];
 exec [label="executor.c / executor.h"]; bi [label="builtins.c / builtins.h"]; utils [label="utils.c / utils.h\\nStrBuf, xmalloc, shell_error"];
 main -> shell [label="#include"]; main -> utils;
 shell -> parser [label="parse_next_pipeline()"]; shell -> exec [label="execute_pipeline()\\njobs_reap()"];
 exec -> bi [label="is_builtin()\\nrun_builtin()"]; exec -> parser [label="uses Command/Pipeline"];
 exec -> shell [label="uses Shell state,\\ng_sigint_flag"]; bi -> shell [label="Shell*"];
 parser -> utils; exec -> utils; bi -> utils; shell -> utils;
}}''')

# 3. High-level flowchart (shell lifecycle) -------------------------------------
dot("03_lifecycle_flow", f'''digraph G {{
 rankdir=TB; node [shape=box, style="rounded,filled", fillcolor="#e8f0fe", {FONT}, fontsize=11]; edge [{FONT}, fontsize=9];
 start [label="Start", shape=oval, fillcolor="#d9ead3"];
 args [label="main(): parse options\\n(-c cmd | script file | none)"];
 init [label="shell_init(): state, isatty()\\nshell_setup_signals() (interactive only)"];
 loop [label="shell_run_stream() loop", shape=diamond, fillcolor="#fff2cc"];
 reap [label="jobs_reap(): report finished\\nbackground jobs"];
 prompt [label="interactive?  print prompt"];
 read [label="getline()", shape=box];
 rd [label="read result?", shape=diamond, fillcolor="#fff2cc"];
 intr [label="EINTR (Ctrl+C):\\nnewline, status 130, redraw"];
 eof [label="EOF (Ctrl+D): print 'exit'"];
 exe [label="shell_execute_line():\\nparse + execute each pipeline"];
 run [label="sh->running ?", shape=diamond, fillcolor="#fff2cc"];
 clean [label="shell_cleanup(); return exit code"];
 end [label="End", shape=oval, fillcolor="#f4cccc"];
 start -> args -> init -> loop; loop -> reap [label="yes"]; reap -> prompt -> read -> rd;
 rd -> exe [label="line"]; rd -> intr [label="interrupted"]; rd -> eof [label="EOF"];
 intr -> loop; exe -> run; run -> loop [label="yes"]; run -> clean [label="no (exit)"];
 eof -> clean; loop -> clean [label="no"]; clean -> end;
}}''')

# 4. Command execution flowchart -----------------------------------------------
dot("04_execution_flow", f'''digraph G {{
 rankdir=TB; node [shape=box, style="rounded,filled", fillcolor="#e8f0fe", {FONT}, fontsize=11]; edge [{FONT}, fontsize=9];
 a [label="execute_pipeline(pipeline)"];
 b [label="single command,\\nforeground?", shape=diamond, fillcolor="#fff2cc"];
 c [label="all words NAME=VALUE?", shape=diamond, fillcolor="#fff2cc"];
 d [label="setenv() in shell\\nstatus 0", fillcolor="#d9ead3"];
 e [label="built-in?", shape=diamond, fillcolor="#fff2cc"];
 f [label="save fd 0/1, apply redirections,\\nrun_builtin() in shell process,\\nrestore fds", fillcolor="#d9ead3"];
 g [label="for each command i:\\npipe() if not last; fork()"];
 h [label="CHILD: reset SIGINT (DFL, or IGN if &),\\ndup2 pipe ends, apply < > >>,\\n/dev/null stdin for first bg cmd"];
 i [label="built-in in pipeline?", shape=diamond, fillcolor="#fff2cc"];
 j [label="run_builtin(); _exit(status)", fillcolor="#d9ead3"];
 k [label="execvp(argv[0]) - PATH search", fillcolor="#f4cccc"];
 l [label="exec failed:\\nENOENT -> 'command not found' / 127\\nother -> strerror / 126", fillcolor="#f4cccc"];
 m [label="PARENT: close unused pipe ends,\\nrecord pid"];
 n [label="background (&)?", shape=diamond, fillcolor="#fff2cc"];
 o [label="jobs_add(): print [id] pid\\nstatus 0, return immediately", fillcolor="#d9ead3"];
 p [label="waitpid() each child (retry on EINTR)\\nstatus = last command:\\nexit code, or 128+signal"];
 q [label="return status  ->  $?", shape=oval, fillcolor="#d9ead3"];
 a -> b; b -> c [label="yes"]; b -> g [label="no"]; c -> d [label="yes"]; c -> e [label="no"];
 e -> f [label="yes"]; e -> g [label="no"]; d -> q; f -> q;
 g -> h [label="pid == 0"]; h -> i; i -> j [label="yes"]; i -> k [label="no"]; k -> l [label="returns"];
 g -> m [label="pid > 0"]; m -> n; n -> o [label="yes"]; n -> p [label="no"]; o -> q; p -> q;
}}''')

# 5. Use-case diagram ----------------------------------------------------------
dot("05_use_case", f'''digraph G {{
 rankdir=LR; {FONT}; node [{FONT}, fontsize=11]; edge [arrowhead=none];
 user [label="User", shape=box, style=filled, fillcolor="#e8f0fe"];
 os [label="Operating\\nSystem", shape=box, style=filled, fillcolor="#eeeeee"];
 subgraph cluster_s {{ label="Simple Shell (mysh)"; style=rounded; node [shape=ellipse, style=filled, fillcolor="#fff2cc"];
  u1 [label="Run external command"]; u2 [label="Use built-in commands\\n(cd, pwd, exit, help)"]; u3 [label="Manage environment\\nvariables"];
  u4 [label="Redirect input/output"]; u5 [label="Build a pipeline"]; u6 [label="Run job in background"];
  u7 [label="Chain commands with ;"]; u8 [label="Interrupt with Ctrl+C"]; u9 [label="Run script / -c string"]; u10 [label="Quit shell (exit / Ctrl+D)"]; u11 [label="Receive error messages"];
 }}
 user -> u1; user -> u2; user -> u3; user -> u4; user -> u5; user -> u6; user -> u7; user -> u8; user -> u9; user -> u10; user -> u11;
 u1 -> os [style=dashed]; u4 -> os [style=dashed]; u5 -> os [style=dashed]; u6 -> os [style=dashed]; u8 -> os [style=dashed];
}}''')

# 7. Data-flow diagram (level 1) -----------------------------------------------
dot("07_dfd_level1", f'''digraph G {{
 rankdir=TB; nodesep=0.35; node [{FONT}, fontsize=11]; edge [{FONT}, fontsize=9];
 user [label="User", shape=box, style=filled, fillcolor="#e8f0fe"];
 p1 [label="1.0\\nRead input", shape=circle, style=filled, fillcolor="#fff2cc"];
 p2 [label="2.0\\nParse & expand", shape=circle, style=filled, fillcolor="#fff2cc"];
 p3 [label="3.0\\nExecute\\npipeline", shape=circle, style=filled, fillcolor="#fff2cc"];
 p4 [label="4.0\\nRun built-in", shape=circle, style=filled, fillcolor="#fff2cc"];
 d1 [label="Environment\\n(environ)", shape=cds, style=filled, fillcolor="#eeeeee"];
 d2 [label="Shell state\\n($?, jobs)", shape=cds, style=filled, fillcolor="#eeeeee"];
 d3 [label="Files / pipes", shape=cds, style=filled, fillcolor="#eeeeee"];
 os [label="OS processes", shape=box, style=filled, fillcolor="#eeeeee"];
 user -> p1 [label="command line"]; p1 -> p2 [label="raw line"]; p2 -> p3 [label="Pipeline\\n(argv, redirs, bg)"];
 d1 -> p2 [label="$VAR values"]; d2 -> p2 [label="$?"]; p3 -> p4 [label="built-in argv"]; p4 -> d1 [label="export/unset/cd"];
 p3 -> os [label="fork/exec"]; os -> p3 [label="exit status"]; p3 -> d2 [label="status, jobs"];
 p3 -> d3 [label="dup2 targets"]; d3 -> p3 [label="input data"]; p3 -> user [label="output / errors"]; p4 -> user [label="output / errors"];
}}''')

# 8. Error-handling flow -------------------------------------------------------
dot("08_error_flow", f'''digraph G {{
 rankdir=TB; node [shape=box, style="rounded,filled", fillcolor="#e8f0fe", {FONT}, fontsize=11]; edge [{FONT}, fontsize=9];
 in [label="Input line"];
 s [label="Parser: syntax valid?", shape=diamond, fillcolor="#fff2cc"];
 se [label="shell_error(msg)\\nstatus = 2\\nrest of line discarded", fillcolor="#f4cccc"];
 r [label="Redirection: open()/dup2() ok?", shape=diamond, fillcolor="#fff2cc"];
 re [label="shell_error(file: strerror)\\nstatus = 1\\ncommand not run", fillcolor="#f4cccc"];
 x [label="execvp() succeeds?", shape=diamond, fillcolor="#fff2cc"];
 xe [label="ENOENT: 'command not found' status 127\\nEACCES etc.: strerror, status 126", fillcolor="#f4cccc"];
 f [label="fork()/pipe() ok?", shape=diamond, fillcolor="#fff2cc"];
 fe [label="shell_error(strerror)\\nreap started children, status 1", fillcolor="#f4cccc"];
 ok [label="Run; status = exit code\\nor 128+signal", fillcolor="#d9ead3"];
 nx [label="Shell prints next prompt\\n(never terminates on errors)", shape=oval, fillcolor="#d9ead3"];
 in -> s; s -> se [label="no"]; s -> f [label="yes"]; f -> fe [label="no"]; f -> r [label="yes"]; r -> re [label="no"]; r -> x [label="yes"];
 x -> xe [label="no"]; x -> ok [label="yes"]; se -> nx; fe -> nx; re -> nx; xe -> nx; ok -> nx;
}}''')

# 6. Sequence diagram (matplotlib) ---------------------------------------------
def sequence():
    actors = ["User", "shell.c\\n(main loop)", "parser.c", "executor.c", "Child 1\\n(cat)", "Child 2\\n(grep)", "Kernel"]
    actors = [a.replace("\\n", "\n") for a in actors]
    xs = [i * 2.3 for i in range(len(actors))]
    msgs = [  # (from, to, text)
        (0, 1, "types: cat file.txt | grep hello"),
        (1, 2, "parse_next_pipeline()"),
        (2, 1, "Pipeline{2 commands}"),
        (1, 3, "execute_pipeline()"),
        (3, 6, "pipe(); fork()  [child 1]"),
        (6, 4, "child created"),
        (3, 6, "fork()  [child 2]"),
        (6, 5, "child created"),
        (4, 4, "dup2(pipe write -> stdout); execvp(\"cat\")"),
        (5, 5, "dup2(pipe read -> stdin); execvp(\"grep\")"),
        (4, 5, "file data flows through pipe"),
        (5, 0, "matching lines written to terminal"),
        (3, 6, "waitpid(child1); waitpid(child2)"),
        (6, 3, "exit statuses"),
        (3, 1, "status of last command ($?)"),
        (1, 0, "prints next prompt"),
    ]
    fig, ax = plt.subplots(figsize=(15, 9.5))
    top, step = 0, 0.55
    for x, a in zip(xs, actors):
        ax.text(x, top, a, ha="center", va="center", fontsize=10, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.4", fc="#fff2cc", ec="#666"))
        ax.plot([x, x], [top - 0.5, -step * (len(msgs) + 1)], color="#999", ls="--", lw=1)
    for i, (a, b, text) in enumerate(msgs):
        y = -step * (i + 1)
        if a == b:
            ax.annotate("", xy=(xs[a] + 0.05, y - 0.22), xytext=(xs[a] + 0.05, y + 0.05),
                        arrowprops=dict(arrowstyle="->", color="#333", connectionstyle="arc3,rad=-0.6"))
            ax.text(xs[a] + 0.3, y - 0.1, text, fontsize=8.5, va="center")
        else:
            ax.annotate("", xy=(xs[b], y), xytext=(xs[a], y),
                        arrowprops=dict(arrowstyle="->", color="#333",
                                        linestyle="--" if b < a else "-"))
            ax.text((xs[a] + xs[b]) / 2, y + 0.08, f"{i+1}. {text}", ha="center", fontsize=8.5)
    ax.set_xlim(-1.3, xs[-1] + 1.6); ax.set_ylim(-step * (len(msgs) + 1.5), 0.8)
    ax.axis("off"); ax.set_title("Sequence diagram: executing  cat file.txt | grep hello", fontsize=12)
    fig.savefig(os.path.join(HERE, "06_sequence.png"), dpi=130, bbox_inches="tight")

sequence()

# ======================= UML-style diagrams (Part-1 deliverables) =========================
from matplotlib.patches import Ellipse, FancyBboxPatch, Rectangle, Circle

def save(fig, name):
    fig.savefig(os.path.join(HERE, name), dpi=170, bbox_inches="tight"); plt.close(fig)

def stick(ax, x, y, label, s=0.5):
    ax.add_patch(Circle((x, y + 1.6*s), 0.28*s, fill=False, lw=1.5))
    ax.plot([x, x], [y + 1.3*s, y + 0.5*s], "k", lw=1.5)
    ax.plot([x - 0.45*s, x + 0.45*s], [y + 1.0*s, y + 1.0*s], "k", lw=1.5)
    ax.plot([x, x - 0.4*s], [y + 0.5*s, y], "k", lw=1.5); ax.plot([x, x + 0.4*s], [y + 0.5*s, y], "k", lw=1.5)
    ax.text(x, y - 0.25, label, ha="center", va="top", fontsize=10, fontweight="bold")

def use_case():
    fig, ax = plt.subplots(figsize=(10.5, 7.3)); ax.set_xlim(0, 15); ax.set_ylim(0, 10.4); ax.axis("off")
    ax.add_patch(Rectangle((2.4, 0.2), 10.2, 10.0, fill=False, lw=1.8))
    ax.text(7.5, 9.95, "Simple Shell (mysh)", ha="center", va="center", fontsize=12, fontweight="bold")
    A, B = 4.3, 9.9
    uc = {"UC1": ("Run external command", A, 8.6), "UC2": ("Use built-in command\n(cd, pwd, exit, help)", A, 7.1),
          "UC3": ("Manage environment\nvariables", A, 5.6), "UC4": ("Run script / -c string /\npiped input", A, 4.1),
          "UC5": ("Quit the shell\n(exit, Ctrl+D)", A, 2.6), "UC6": ("Interrupt with Ctrl+C", A, 1.1),
          "UC12": ("Search PATH", B, 9.3), "UC7": ("Redirect input/output\n( < > >> )", B, 7.7),
          "UC8": ("Build a pipeline ( | )", B, 6.5), "UC9": ("Run in background ( & )", B, 5.3),
          "UC10": ("Chain commands ( ; )", B, 4.1), "UC11": ("Report invalid command /\nsyntax error", B, 2.9)}
    for k, (t, x, y) in uc.items():
        ax.add_patch(Ellipse((x, y), 2.9, 0.95, fc="#fff8e1", ec="#444", lw=1.3))
        ax.text(x, y, t, ha="center", va="center", fontsize=7.6)
    stick(ax, 1.0, 4.6, "User")
    for k in ("UC1", "UC2", "UC3", "UC4", "UC5", "UC6"):
        _, x, y = uc[k]; ax.plot([1.4, x - 1.45], [5.5, y], color="#333", lw=1)
    ax.add_patch(FancyBboxPatch((13.2, 8.05), 1.4, 1.1, boxstyle="round,pad=0.05", fc="#eeeeee", ec="#444"))
    ax.text(13.9, 8.6, "<<system>>\nOperating\nSystem", ha="center", va="center", fontsize=8.5, fontweight="bold")
    ax.plot([13.2, A + 1.45], [8.6, 8.6], color="#333", lw=1)
    def edge_pt(c, o):   # point on ellipse c (w=2.9,h=0.95) in the direction of o
        dx, dy = o[0] - c[0], o[1] - c[1]; L = ((dx / 1.45) ** 2 + (dy / 0.475) ** 2) ** 0.5
        return (c[0] + dx / L, c[1] + dy / L)
    def rel(a, b, label, t=0.5):
        ca, cb = (uc[a][1], uc[a][2]), (uc[b][1], uc[b][2])
        p, q = edge_pt(ca, cb), edge_pt(cb, ca)
        ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="->", ls="--", color="#1a56a0", lw=1.1, shrinkA=0, shrinkB=0))
        ax.text(p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, label, fontsize=7.2, color="#1a56a0", ha="center", va="center",
                bbox=dict(fc="white", ec="none", pad=0.5))
    for k, tt in (("UC7", 0.5), ("UC8", 0.42), ("UC9", 0.36), ("UC10", 0.31), ("UC11", 0.27)): rel(k, "UC1", "<<extend>>", tt)
    rel("UC1", "UC12", "<<include>>", 0.5)
    ax.set_title("UML use-case diagram: Simple Shell", fontsize=12)
    save(fig, "05_use_case.png")

def sequence_diagram(fname, title, parts, msgs, frames=(), notes=()):
    """Sequence diagram drawn in inch units so text stays readable when the page scales the picture.
    msgs: (src, dst, text[, style]); style in {'', 'ret', 'async'}; src == dst is a self message."""
    import textwrap
    n = len(parts); W = 10.6; left = right = 0.85
    gap = (W - left - right) / (n - 1); xs = [left + i * gap for i in range(n)]
    LH, FS = 0.155, 8.6
    y = -0.7; rows = []
    for i, m in enumerate(msgs):
        a, b, text = m[0], m[1], m[2]; style = m[3] if len(m) > 3 else ""
        if a == b:
            chars = max(22, int((W - xs[a] - 0.7) / 0.066))
        else:
            chars = max(15, int((abs(xs[b] - xs[a]) - 0.15) / 0.066))
        lines = textwrap.wrap(f"{i+1}. {text}", chars, break_long_words=False, break_on_hyphens=False) or [f"{i+1}."]
        y -= LH * len(lines) + 0.22
        rows.append((y, lines, a, b, style))
    H = -y + 0.55
    fig, ax = plt.subplots(figsize=(W, H + 1.3))
    for x, (p, kind) in zip(xs, parts):
        label = p.replace("\\n", "\n")
        if kind == "actor":
            stick(ax, x, 0.15, "", s=0.34); ax.text(x, 0.07, label, ha="center", va="top", fontsize=9, fontweight="bold")
        else:
            ax.text(x, 0.38, label, ha="center", va="center", fontsize=8.8, fontweight="bold",
                    bbox=dict(boxstyle="square,pad=0.35", fc="#fff2cc", ec="#444"))
        ax.plot([x, x], [-0.05, -H], color="#888", ls="--", lw=0.9)
    for (fa, fb, label) in frames:
        top = rows[fa][0] + LH * len(rows[fa][1]) + 0.12; bot = rows[fb][0] - 0.14
        ax.add_patch(Rectangle((0.2, bot), W - 0.4, top - bot, fill=False, ec="#7a3e9d", lw=1.1))
        ax.text(W - 0.3, top - 0.03, label, fontsize=8, color="#7a3e9d", va="top", ha="right", fontweight="bold")
    for (yy, lines, a, b, style) in rows:
        if a == b:
            ax.add_patch(Rectangle((xs[a] - 0.04, yy - 0.12), 0.08, 0.2, fc="#ddd", ec="#444"))
            ax.annotate("", xy=(xs[a] + 0.04, yy - 0.1), xytext=(xs[a] + 0.04, yy + 0.06),
                        arrowprops=dict(arrowstyle="->", color="#222", connectionstyle="arc3,rad=-1.2"))
            ax.text(xs[a] + 0.28, yy + LH * (len(lines) - 1) / 2, "\n".join(lines), fontsize=FS, va="center", ha="left", linespacing=1.15)
        else:
            ax.annotate("", xy=(xs[b], yy), xytext=(xs[a], yy),
                        arrowprops=dict(arrowstyle="->" if style != "async" else "-|>", color="#222", lw=1.0,
                                        linestyle="--" if style == "ret" else "-"))
            ax.text((xs[a] + xs[b]) / 2, yy + 0.05, "\n".join(lines), ha="center", va="bottom", fontsize=FS, linespacing=1.15)
    ax.set_xlim(0, W); ax.set_ylim(-H - 0.1, 1.2); ax.axis("off")
    ax.set_title(title, fontsize=10.5, fontweight="bold", pad=4)
    save(fig, fname)

def sequences():
    P = [("User", "actor"), ("shell.c\\n(main loop)", "obj"), ("parser.c", "obj"), ("executor.c", "obj"),
         ("Child 1\\ncat", "obj"), ("Child 2\\ngrep", "obj"), ("Kernel", "obj")]
    sequence_diagram("06_sequence.png", "SD-1  Execute a foreground pipeline:  cat file.txt | grep hello", P, [
        (0, 1, "types: cat file.txt | grep hello"), (1, 2, "parse_next_pipeline(&cursor, $?)"),
        (2, 1, "PARSE_OK, Pipeline{2 commands}", "ret"), (1, 3, "execute_pipeline(sh, &pl)"),
        (3, 6, "pipe(fd); fork()  -> child 1"), (3, 6, "fork()  -> child 2"),
        (4, 4, "dup2(fd[1], 1); execvp(\"cat\")"), (5, 5, "dup2(fd[0], 0); execvp(\"grep\")"),
        (3, 3, "close pipe ends in parent"), (4, 5, "file data through the pipe"),
        (5, 0, "matching lines written to terminal"), (3, 6, "waitpid(child 1); waitpid(child 2)"),
        (6, 3, "exit statuses", "ret"), (3, 1, "return status of last command", "ret"), (1, 0, "prints next prompt")])
    P2 = [("User", "actor"), ("shell.c", "obj"), ("parser.c", "obj"), ("executor.c", "obj"), ("Child\\nsleep 5", "obj"), ("Kernel", "obj")]
    sequence_diagram("09_seq_background.png", "SD-2  Background job:  sleep 5 &   and later completion notice", P2, [
        (0, 1, "types: sleep 5 &"), (1, 2, "parse_next_pipeline()"), (2, 1, "Pipeline{background=1}", "ret"),
        (1, 3, "execute_pipeline()"), (3, 5, "fork()"), (4, 4, "SIGINT ignored; stdin = /dev/null; execvp(\"sleep\")"),
        (3, 3, "jobs_add(): store pid, print \"[1] pid\""), (3, 1, "return 0 immediately", "ret"), (1, 0, "prompt returns at once"),
        (4, 5, "sleep ends, exits (status 0)"), (0, 1, "later: presses Enter"), (1, 3, "jobs_reap(): waitpid(-1, WNOHANG)"),
        (5, 3, "pid of finished child", "ret"), (3, 0, "prints \"[1]+ Done  sleep 5\"; frees job entry")])
    P3 = [("User", "actor"), ("Terminal /\\nkernel", "obj"), ("shell.c", "obj"), ("executor.c", "obj"), ("Child\\nsleep 30", "obj")]
    sequence_diagram("10_seq_ctrlc.png", "SD-3  Ctrl+C while a foreground job runs", P3, [
        (0, 2, "types: sleep 30"), (2, 3, "execute_pipeline()"), (3, 4, "fork(); child: SIGINT = default; execvp"),
        (3, 3, "wait_foreground(): waitpid(child)"), (0, 1, "presses Ctrl+C"),
        (1, 2, "SIGINT -> sigint_handler(): g_sigint_flag = 1 (only)", "async"), (1, 4, "SIGINT -> default action: terminate", "async"),
        (4, 3, "waitpid returns: WIFSIGNALED, sig = SIGINT", "ret"), (3, 3, "status = 128 + 2 = 130; print newline"),
        (3, 2, "return 130", "ret"), (2, 0, "prints next prompt; shell is still running")])
    P4 = [("User", "actor"), ("shell.c", "obj"), ("parser.c", "obj"), ("executor.c", "obj"), ("Child", "obj"), ("Kernel", "obj")]
    sequence_diagram("11_seq_error.png", "SD-4  Error paths: syntax error, command not found, redirection failure", P4, [
        (0, 1, "types: echo \"oops"), (1, 2, "parse_next_pipeline()"), (2, 1, "PARSE_ERROR \"unterminated double quote\"", "ret"),
        (1, 0, "stderr: mysh: syntax error: unterminated double quote; $? = 2; rest of line dropped"),
        (0, 1, "types: invalidcommand"), (1, 3, "execute_pipeline()"), (3, 5, "fork()"), (4, 5, "execvp(\"invalidcommand\")"),
        (5, 4, "returns -1, errno = ENOENT", "ret"), (4, 0, "stderr: mysh: invalidcommand: command not found; _exit(127)"),
        (3, 1, "waitpid -> status 127; $? = 127", "ret"),
        (0, 1, "types: cat < missing.txt"), (1, 3, "execute_pipeline()"), (3, 5, "fork()"),
        (4, 4, "apply_redirections(): open(\"missing.txt\") fails (ENOENT)"),
        (4, 0, "stderr: mysh: missing.txt: No such file or directory; _exit(1)"), (3, 1, "waitpid -> status 1; $? = 1", "ret"),
        (1, 0, "prompt again - the shell never terminates because of an error")],
        frames=[(0, 3, "Scenario 1: syntax error"), (4, 10, "Scenario 2: command not found"), (11, 16, "Scenario 3: redirection failure")])

use_case(); sequences()

# UML component diagram with provided/required interfaces
dot("02_components", f'''digraph G {{
 rankdir=TB; nodesep=0.6; ranksep=0.8; node [{FONT}, fontsize=10]; edge [{FONT}, fontsize=8];
 node [shape=component, style=filled, fillcolor="#fff2cc"];
 main [label="<<component>>\\nmain\\n(main.c)"]; shell [label="<<component>>\\nShell Core\\n(shell.c)"];
 parser [label="<<component>>\\nParser\\n(parser.c)"]; exec [label="<<component>>\\nExecutor\\n(executor.c)"];
 bi [label="<<component>>\\nBuilt-ins\\n(builtins.c)"]; utils [label="<<component>>\\nUtilities\\n(utils.c)"];
 node [shape=circle, width=0.18, label="", style=filled, fillcolor=white];
 i_shell [xlabel="IShell\\nshell_run_stream()\\nshell_execute_line()"]; i_parse [xlabel="IParser\\nparse_next_pipeline()\\npipeline_free()"];
 i_exec [xlabel="IExecutor\\nexecute_pipeline()\\njobs_reap()"]; i_bi [xlabel="IBuiltins\\nis_builtin()\\nrun_builtin()"];
 i_util [xlabel="IUtil\\nxmalloc() shell_error()\\nStrBuf, is_valid_name()"];
 node [shape=box, style="rounded,filled", fillcolor="#e8f0fe", width=0.4, height=0.3]; os [label="<<external>>\\nPOSIX OS interface\\nfork execvp pipe dup2\\nwaitpid sigaction chdir"];
 shell -> i_shell [arrowhead=none]; i_shell -> main [arrowhead=open, style=dashed, label="requires"];
 parser -> i_parse [arrowhead=none]; i_parse -> shell [arrowhead=open, style=dashed]; i_parse -> exec [arrowhead=open, style=dashed, label="Pipeline type"];
 exec -> i_exec [arrowhead=none]; i_exec -> shell [arrowhead=open, style=dashed];
 bi -> i_bi [arrowhead=none]; i_bi -> exec [arrowhead=open, style=dashed];
 utils -> i_util [arrowhead=none]; i_util -> parser [arrowhead=open, style=dashed]; i_util -> exec [arrowhead=open, style=dashed]; i_util -> bi [arrowhead=open, style=dashed];
 exec -> os [arrowhead=open, style=dashed, label="requires"]; bi -> os [arrowhead=open, style=dashed]; shell -> os [arrowhead=open, style=dashed, label="signals"];
}}''')

# Trust boundaries / security data-flow
dot("12_trust_boundaries", f'''digraph G {{
 rankdir=TB; compound=true; nodesep=0.3; ranksep=0.55; node [shape=box, style="rounded,filled", {FONT}, fontsize=10]; edge [{FONT}, fontsize=8];
 subgraph cluster_u {{ label="Trust zone A: untrusted input"; style=dashed; color="#c0392b"; fontcolor="#c0392b"; {FONT};
   user [label="User keystrokes\\n(terminal)", fillcolor="#fadbd8"]; script [label="Script file /\\n-c string / stdin", fillcolor="#fadbd8"]; }}
 subgraph cluster_s {{ label="Trust zone B: mysh process (runs with the invoking user's rights)"; style=dashed; color="#1e8449"; fontcolor="#1e8449"; {FONT};
   parser [label="Parser\\nSR-01 SR-02 SR-06 SR-07", fillcolor="#d5f5e3"]; exec [label="Executor\\nargv only, no system()\\nSR-01 SR-03 SR-05 SR-08 SR-10", fillcolor="#d5f5e3"];
   bi [label="Built-ins\\nname validation SR-07", fillcolor="#d5f5e3"]; sig [label="Signal policy SR-09", fillcolor="#d5f5e3"]; }}
 subgraph cluster_o {{ label="Trust zone C: operating system (enforces access control)"; style=dashed; color="#1f618d"; fontcolor="#1f618d"; {FONT};
   fs [label="File system\\n(permissions, umask)", fillcolor="#d6eaf8"]; env [label="Environment\\n(inherited by children)", fillcolor="#d6eaf8"]; kern [label="Process / signal /\\ndescriptor tables", fillcolor="#d6eaf8"]; }}
 prog [label="Executed programs\\n(same uid, only fds 0-2)", fillcolor="#fdebd0"];
 user -> parser [label="command text"]; script -> parser [label="command text"]; parser -> exec [label="Pipeline (argv vectors)"];
 parser -> bi [style=invis]; exec -> bi [label="built-in argv"]; exec -> fs [label="open() with mode 0644 & ~umask"]; bi -> env [label="setenv/unsetenv"];
 exec -> kern [label="fork / execvp / waitpid"]; kern -> prog [label="new process"]; user -> sig [label="Ctrl+C / Ctrl+Z", style=dashed]; sig -> kern [style=dashed];
}}''')

print("diagrams written to", HERE)
