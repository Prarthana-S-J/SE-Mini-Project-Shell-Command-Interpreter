#!/usr/bin/env python3
"""interactive_test.py - System tests that drive mysh through a pseudo-terminal.

These tests exercise behaviour that only exists on a real terminal: the prompt,
Ctrl+C, Ctrl+D, Ctrl+Z and background-job notifications.  (Member 4 / Member 3)

Usage:  python3 tests/interactive_test.py      (after `make`)
Output line format:  <ID> <REQ> PASS|FAIL <description>
"""
import os, pty, re, select, signal, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MYSH = os.environ.get("MYSH", os.path.join(ROOT, "mysh"))
PROMPT = re.compile(rb"mysh:[^\r\n]*\$ ")
RESULTS = os.path.join(ROOT, "tests", "results_interactive.txt")

results = []
ENABLED_FILE = os.environ.get("MYSH_ENABLED_FILE", os.path.join(ROOT, "tests", "enabled_tests.txt"))


def enabled(tid):
    """tests/enabled_tests.txt lists the test IDs that must pass at the current development stage
    (see stories/README.md). 'ALL' or a missing file enables everything."""
    if os.environ.get("MYSH_ENABLE_ALL") or not os.path.exists(ENABLED_FILE):
        return True
    ids = {l.strip() for l in open(ENABLED_FILE)}
    return "ALL" in ids or tid in ids


class Session:
    def __init__(self):
        self.cwd = tempfile.mkdtemp()
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.chdir(self.cwd)
            os.execv(MYSH, [MYSH])
        self.buf = b""

    def read_until(self, pattern, timeout=5.0):
        """Read until regex `pattern` matches the unread buffer; return matched text."""
        deadline = time.time() + timeout
        pat = re.compile(pattern) if isinstance(pattern, bytes) else pattern
        while time.time() < deadline:
            m = pat.search(self.buf)
            if m:
                out = self.buf[: m.end()]
                self.buf = self.buf[m.end():]
                return out
            r, _, _ = select.select([self.fd], [], [], 0.1)
            if r:
                try:
                    data = os.read(self.fd, 4096)
                except OSError:
                    break
                if not data:
                    break
                self.buf += data
        return None

    def send(self, s):
        os.write(self.fd, s if isinstance(s, bytes) else s.encode())

    def wait_exit(self, timeout=5.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            p, st = os.waitpid(self.pid, os.WNOHANG)
            if p:
                return os.WEXITSTATUS(st) if os.WIFEXITED(st) else -1
            time.sleep(0.05)
        return None

    def kill(self):
        try:
            os.kill(self.pid, signal.SIGKILL)
            os.waitpid(self.pid, 0)
        except (OSError, ChildProcessError):
            pass


def record(tid, req, ok, desc, detail=""):
    if not enabled(tid):
        line = f"{tid} {req} SKIP {desc}"
        print(line)
        results.append((None, line))
        return
    line = f"{tid} {req} {'PASS' if ok else 'FAIL'} {desc}"
    print(line)
    if not ok and detail:
        print("      -> " + detail)
    results.append((ok, line))


def test_prompt():
    s = Session()
    got = s.read_until(PROMPT)
    record("ST-01", "FR-01", got is not None, "interactive prompt is displayed at start-up",
           f"buffer={s.buf!r}")
    s.send("echo hello-from-shell\n")
    out = s.read_until(PROMPT)
    ok = out is not None and b"hello-from-shell" in out
    record("ST-02", "FR-01,FR-05", ok, "command output is shown and the prompt returns", f"out={out!r}")
    s.kill()


def test_ctrl_c_prompt():
    s = Session(); s.read_until(PROMPT)
    s.send(b"partial text"); time.sleep(0.2)
    s.send(b"\x03")
    got = s.read_until(PROMPT)
    s.send("echo still-alive\n")
    out = s.read_until(PROMPT)
    ok = got is not None and out is not None and b"still-alive" in out
    record("ST-03", "FR-21,SR-09", ok, "Ctrl+C at the prompt abandons the line; shell keeps running",
           f"got={got!r} out={out!r}")
    s.kill()


def test_ctrl_c_foreground():
    s = Session(); s.read_until(PROMPT)
    t0 = time.time()
    s.send("sleep 30\n"); time.sleep(0.6)
    s.send(b"\x03")
    got = s.read_until(PROMPT, timeout=4)
    took = time.time() - t0
    s.send("echo $?\n")
    out = s.read_until(PROMPT)
    ok = got is not None and took < 5 and out is not None and b"130" in out
    record("ST-04", "FR-21,FR-06,SR-09", ok,
           "Ctrl+C kills the foreground job (status 130) but not the shell",
           f"got={got!r} took={took:.1f}s status-out={out!r}")
    s.kill()


def test_background():
    s = Session(); s.read_until(PROMPT)
    s.send("sleep 1 &\n")
    out = s.read_until(PROMPT)
    ok1 = out is not None and re.search(rb"\[1\] \d+", out) is not None
    time.sleep(1.5)
    s.send("\n")
    out2 = s.read_until(PROMPT)
    ok2 = out2 is not None and b"Done" in out2 and b"sleep 1" in out2
    record("ST-05", "FR-20", ok1 and ok2,
           "background job prints [id] pid, and a Done notice appears after it finishes",
           f"start={out!r} later={out2!r}")
    s.kill()


def test_ctrl_d():
    s = Session(); s.read_until(PROMPT)
    s.send(b"\x04")
    got = s.read_until(rb"exit")
    rc = s.wait_exit()
    record("ST-06", "FR-22", got is not None and rc == 0,
           "Ctrl+D (EOF) prints 'exit' and terminates the shell with status 0",
           f"got={got!r} rc={rc}")
    s.kill()


def test_bg_survives_ctrl_c():
    s = Session(); s.read_until(PROMPT)
    marker = os.path.join(s.cwd, "bg_finished.txt")
    s.send("sh -c 'sleep 2; echo finished > bg_finished.txt' &\n"); s.read_until(PROMPT)
    s.send(b"\x03"); s.read_until(PROMPT)
    time.sleep(2.6)
    s.send("\n")
    out = s.read_until(PROMPT)
    # The marker file only exists if the job ran to completion (was not killed by SIGINT).
    ok = out is not None and b"Done" in out and os.path.exists(marker)
    record("ST-07", "FR-21,FR-20", ok,
           "Ctrl+C at the prompt does not terminate a running background job (job completes its work)",
           f"out={out!r} marker={os.path.exists(marker)}")
    s.kill()


def test_ctrl_z_ignored():
    s = Session(); s.read_until(PROMPT)
    s.send("sleep 1\n"); time.sleep(0.3)
    s.send(b"\x1a")
    got = s.read_until(PROMPT, timeout=4)
    record("ST-08", "FR-21,SR-09", got is not None,
           "Ctrl+Z does not stop the foreground job or hang the shell (no job control)",
           f"got={got!r}")
    s.kill()


def test_exit_status():
    s = Session(); s.read_until(PROMPT)
    s.send("exit 4\n")
    rc = s.wait_exit()
    record("ST-09", "FR-10", rc == 4, "'exit 4' terminates the interactive shell with status 4",
           f"rc={rc}")
    s.kill()


def test_bg_survives_shell_signal_isolation():
    """A background job must not be killed by Ctrl+C sent while a foreground job runs."""
    s = Session(); s.read_until(PROMPT)
    marker = os.path.join(s.cwd, "bg_finished2.txt")
    s.send("sh -c 'sleep 2; echo finished > bg_finished2.txt' &\n"); s.read_until(PROMPT)
    s.send("sleep 30\n"); time.sleep(0.5)
    s.send(b"\x03"); s.read_until(PROMPT, timeout=4)
    time.sleep(2.3)
    s.send("\n")
    out = s.read_until(PROMPT)
    ok = out is not None and b"Done" in out and os.path.exists(marker)
    record("ST-11", "FR-21,FR-20", ok,
           "Ctrl+C aimed at a foreground job leaves the background job running to completion",
           f"out={out!r} marker={os.path.exists(marker)}")
    s.kill()


FUNC_IDS = {"test_prompt": ("ST-01", "ST-02"), "test_ctrl_c_prompt": ("ST-03",), "test_ctrl_c_foreground": ("ST-04",),
            "test_background": ("ST-05",), "test_ctrl_d": ("ST-06",), "test_bg_survives_ctrl_c": ("ST-07",),
            "test_ctrl_z_ignored": ("ST-08",), "test_exit_status": ("ST-09",),
            "test_bg_survives_shell_signal_isolation": ("ST-11",)}

if __name__ == "__main__":
    if not os.access(MYSH, os.X_OK):
        print(f"mysh binary not found at {MYSH} (run make first)")
        sys.exit(2)
    print("== Interactive (pseudo-terminal) system tests for mysh ==")
    for fn in (test_prompt, test_ctrl_c_prompt, test_ctrl_c_foreground, test_background,
               test_ctrl_d, test_bg_survives_ctrl_c, test_ctrl_z_ignored, test_exit_status,
               test_bg_survives_shell_signal_isolation):
        try:
            fn()
        except Exception as e:  # keep going so one broken test cannot hide the others
            for tid in FUNC_IDS.get(fn.__name__, (fn.__name__,)):
                if not any(l.startswith(tid + " ") for _, l in results):
                    record(tid, "-", False, "test crashed", repr(e))
    passed = sum(1 for ok, _ in results if ok is True)
    skipped = sum(1 for ok, _ in results if ok is None)
    failed = len(results) - passed - skipped
    summary = f"INTERACTIVE SUMMARY: {len(results) - skipped} run, {passed} passed, {failed} failed" + (f", {skipped} skipped (not implemented yet)" if skipped else "")
    print(summary)
    with open(RESULTS, "w") as f:
        f.write("\n".join(l for _, l in results) + "\n" + summary + "\n")
    sys.exit(0 if failed == 0 else 1)
