#!/bin/bash
# run_tests.sh - Functional / integration / system tests for mysh (Member 4)
#
# Usage:  bash tests/run_tests.sh          (from the project root, after `make`)
#         MYSH=/path/to/mysh bash tests/run_tests.sh
#
# Every test prints:  <ID> <REQ> PASS|FAIL <description>
# A summary line is printed at the end; exit status is 1 if any test failed.
# Results are also written to tests/results_functional.txt

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MYSH="${MYSH:-$ROOT/mysh}"
[ -x "$MYSH" ] || { echo "mysh binary not found at $MYSH (run make first)"; exit 2; }
MYSH="$(cd "$(dirname "$MYSH")" && pwd)/$(basename "$MYSH")"

W="$(mktemp -d)"; W="$(cd "$W" && pwd -P)"
trap 'rm -rf "$W"' EXIT
RESULTS="$ROOT/tests/results_functional.txt"
TSV="$ROOT/tests/results_functional.tsv"
: > "$RESULTS"; : > "$TSV"
declare -A META_CMD META_EXP
meta() { META_CMD["$1"]="$2"; META_EXP["$1"]="$3"; }
esc() { local v="$1"; v="${v//$'\n'/\\n}"; v="${v//$'\t'/ }"; printf '%s' "$v"; }

pass=0; fail=0; skipped=0

# Story-by-story development (see stories/README.md): tests/enabled_tests.txt lists the test IDs that must
# pass at the current stage; other tests are reported as SKIP. The file contains "ALL" in the finished product.
# MYSH_ENABLE_ALL=1 runs every test as a real pass/fail check regardless of the list.
ENABLED_FILE="${MYSH_ENABLED_FILE:-$ROOT/tests/enabled_tests.txt}"
is_enabled() {
    [ -n "$MYSH_ENABLE_ALL" ] || [ ! -f "$ENABLED_FILE" ] || grep -qx 'ALL' "$ENABLED_FILE" || grep -qx "$1" "$ENABLED_FILE"
}

# ---- test fixtures ---------------------------------------------------------
mkdir -p "$W/sub" "$W/bin"
printf 'hello world\nfoo\nhello again\n' > "$W/file.txt"
printf 'from input\n'                     > "$W/input.txt"
printf '#!/bin/sh\necho not-executable\n' > "$W/noexec.sh"; chmod 644 "$W/noexec.sh"
printf '#!/bin/sh\necho tool-ran\n'       > "$W/bin/hello_tool"; chmod 755 "$W/bin/hello_tool"
cp "$ROOT/demo/demo.mysh" "$W/demo.mysh" 2>/dev/null

# ---- helpers ---------------------------------------------------------------
record() {  # id req ok desc [detail]
    local status=PASS
    if ! is_enabled "$1"; then status=SKIP; skipped=$((skipped+1))
    elif [ "$3" -ne 0 ]; then status=FAIL; fail=$((fail+1)); else pass=$((pass+1)); fi
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$status" "$4" "$(esc "${META_CMD[$1]}")" "$(esc "${META_EXP[$1]}")" >> "$TSV"
    echo "$1 $2 $status $4" | tee -a "$RESULTS"
    if [ "$status" = FAIL ] && [ -n "$5" ]; then echo "      -> $5" | tee -a "$RESULTS"; fi
}

# t ID REQ "description" "command string" "expected stdout" [expected rc] [stderr substring]
t() {
    local id="$1" req="$2" desc="$3" cmd="$4" exp="$5" erc="${6:-0}" esub="$7"
    local out err rc
    meta "$id" "$cmd" "$exp$( [ "$erc" != 0 ] && printf ' [exit status %s]' "$erc")$( [ -n "$esub" ] && printf ' [stderr contains: %s]' "$esub")"
    out="$(cd "$W" && "$MYSH" -c "$cmd" 2>"$W/.err")"; rc=$?
    err="$(cat "$W/.err")"
    local ok=0 why=""
    [ "$out" = "$exp" ] || { ok=1; why="stdout was [$out], expected [$exp]"; }
    [ "$rc" = "$erc" ]  || { ok=1; why="$why; rc was $rc, expected $erc"; }
    if [ -n "$esub" ]; then
        case "$err" in *"$esub"*) ;; *) ok=1; why="$why; stderr [$err] lacks [$esub]";; esac
    fi
    record "$id" "$req" "$ok" "$desc" "$why"
}


# ---- metadata for tests that are not expressed through t() ---------------------
meta TC-61 'echo $$'                                   'a numeric process id'
meta TC-34 'help'                                      'usage lines for cd, pwd, exit, help, export, unset, env plus operator summary; status 0'
meta TC-36 'sleep 2 & echo started'                    'prints "started" in < 1.5 s (does not wait 2 s)'
meta TC-74 'sleep 1 | sleep 1 & echo bg-pipeline'      'prints "bg-pipeline" in < 0.8 s'
meta TC-75 'echo bgdata > bg.txt & sleep 0.5; cat bg.txt' 'bgdata'
meta TC-50 'mysh script.mysh   (script: echo line1 / echo line2)' 'line1, line2'
meta TC-51 "printf 'echo a\\necho b\\n' | mysh"          'a, b and no prompt text'
meta TC-52 "printf 'false\\n' | mysh; echo \$?"          'exit status 1'
meta TC-53 'mysh exit.mysh   (script: echo first / exit 5 / echo never)' 'first; exit status 5; "never" not printed'
meta TC-62 'mysh -c'                                   'usage message; exit status 2'
meta TC-63 'mysh /no/such/script'                      'error message; exit status 127'
meta TC-76 'mysh --version'                            'line beginning with "mysh"'
meta TC-54 'echo 1 2 3 ... 2000  (2000 arguments)'     'exactly 2000 words printed'
meta TC-55 'echo <100000 x "a">'                       '100001 bytes printed'
meta TC-77 'true | true;  (repeated 300 times) echo survived' 'survived'
meta ST-10 'mysh demo/demo.mysh'                       'all documented demo outputs present; exit status 0'

echo "== Functional / integration / system tests for mysh =="
echo "shell under test: $MYSH"

# ---- Basic execution (FR-05, FR-06, FR-09) ----------------------------------
t TC-01 FR-09 "pwd prints the working directory"               'pwd' "$W"
t TC-02 FR-05 "ls lists named files"                            'ls file.txt input.txt' $'file.txt\ninput.txt'
t TC-03 FR-05 "echo Hello prints its argument"                  'echo Hello' 'Hello'
t TC-10 FR-05 "cat file.txt prints the file"                    'cat file.txt' $'hello world\nfoo\nhello again'
t TC-30 FR-06 "\$? reflects exit status of false then true"     'false; echo $?; true; echo $?' $'1\n0'
t TC-56 FR-06 "child killed by signal gives status 128+sig"     'sh -c "kill -9 \$\$"; echo $?' '137' 0 'Killed'

# ---- cd (FR-08) --------------------------------------------------------------
t TC-04 FR-08 "cd sub then cd .. returns to start"              'cd sub; pwd; cd ..; pwd' $"$W/sub"$'\n'"$W"
t TC-05 FR-08 "cd to a missing directory reports an error"      'cd nosuchdir; echo $?' '1' 0 'No such file or directory'
t TC-06 FR-08 "cd with no argument goes to \$HOME"              "export HOME=$W/sub; cd; pwd" "$W/sub"
t TC-07 FR-08 "cd - returns to previous directory and prints it" 'cd sub; cd -' "$W"
t TC-65 FR-08 "cd with too many arguments fails"                'cd a b; echo $?' '1' 0 'too many arguments'

# ---- Invalid commands (FR-07) -----------------------------------------------
t TC-08 FR-07 "unknown command -> 127 and message"              'invalidcommand; echo $?' '127' 0 'command not found'
t TC-09 FR-07 "non-executable file -> 126 and message"          './noexec.sh; echo $?' '126' 0 'Permission denied'
t TC-66 FR-07 "missing path with slash -> No such file"         './nothere; echo $?' '127' 0 'No such file or directory'
t TC-67 FR-07 "directory cannot be executed -> 126 and message" './sub; echo $?' '126' 0 'Permission denied'

# ---- Redirection (FR-14..FR-17) ---------------------------------------------
t TC-11 FR-16 "cat < input.txt reads stdin from file"           'cat < input.txt' 'from input'
t TC-12 FR-14 "echo hello > output.txt creates the file"        'echo hello > output.txt; cat output.txt' 'hello'
t TC-13 FR-14 "> truncates an existing file"                    'echo one > t.txt; echo two > t.txt; cat t.txt' 'two'
t TC-14 FR-15 ">> appends to an existing file"                  'echo one > a.txt; echo two >> a.txt; cat a.txt' $'one\ntwo'
t TC-15 FR-15 ">> creates the file when absent"                 'echo x >> new_app.txt; cat new_app.txt' 'x'
t TC-16 FR-17 "< missing file: error, status 1, no crash"       'cat < missing.txt; echo $?' '1' 0 'missing.txt: No such file'
t TC-17 FR-17 "> into a missing directory: error, status 1"     'echo hi > nodir/x.txt; echo $?' '1' 0 'No such file or directory'
t TC-70 FR-04 "redirection with no command is rejected"         '> lonely.txt' '' 2 'redirection without a command'
t TC-71 FR-14 "spaces around > are optional"                    'echo compact>c.txt; cat c.txt' 'compact'

# ---- Pipes (FR-18) ------------------------------------------------------------
t TC-18 FR-18 "cat file.txt | grep hello"                       'cat file.txt | grep hello' $'hello world\nhello again'
t TC-19 FR-18 "three-stage pipeline printf | sort | uniq"       'printf "b\na\nb\n" | sort | uniq' $'a\nb'
t TC-20 FR-18 "pipeline combined with < and >"                  'sort < file.txt | head -n 1 > first.txt; cat first.txt' 'foo'
t TC-21 FR-18 "built-in inside a pipeline (pwd | cat)"          'pwd | cat' "$W"
t TC-22 FR-14 "built-in with output redirection (pwd > f)"      'pwd > pwd.txt; cat pwd.txt' "$W"
t TC-57 FR-18 "ten-stage pipeline"                              'echo x | cat | cat | cat | cat | cat | cat | cat | cat | cat' 'x'
t TC-58 FR-18 "failing first stage does not hang the pipeline"  'nosuchcmd | cat; echo $?' '0' 0 'command not found'

# ---- Environment / expansion (FR-12, FR-13) ---------------------------------
t TC-23 FR-12 "export then \$VAR"                               'export FOO=bar; echo $FOO' 'bar'
t TC-24 FR-12 "exported variable is visible to child processes" 'export FOO=bar; sh -c "echo \$FOO"' 'bar'
t TC-25 FR-12 "NAME=VALUE assignment then \$NAME"               'GREET=hi; echo $GREET' 'hi'
t TC-26 FR-12 "unset removes a variable"                        'export A=1; unset A; echo "[$A]"' '[]'
t TC-27 FR-12 "env lists exported variables"                    'export ZZ_TEST=1; env | grep ZZ_TEST' 'ZZ_TEST=1'
t TC-28 FR-13 "\${NAME} form"                                   'X=ab; echo ${X}cd' 'abcd'
t TC-29 FR-13 "unset variable expands to nothing (word dropped)" 'echo a $NOPE_VAR b' 'a b'
t TC-60 FR-13 "~ expands to \$HOME"                             'export HOME=/tmp; echo ~ ~/x' '/tmp /tmp/x'
t TC-64 FR-12 "export with invalid identifier fails"            'export 1x=3; echo $?' '1' 0 'not a valid identifier'
t TC-38 FR-13 "double quotes allow expansion"                   'X=w; echo "hi $X"' 'hi w'
t TC-72 FR-13 "single quotes suppress expansion"                "echo '\$HOME'" '$HOME'

# \$\$ check is done separately (value varies)
out="$(cd "$W" && "$MYSH" -c 'echo $$' 2>/dev/null)"
case "$out" in ''|*[!0-9]*) record TC-61 FR-13 1 "\$\$ expands to a numeric PID" "got [$out]";;
                *)          record TC-61 FR-13 0 "\$\$ expands to a numeric PID";; esac

# ---- Built-ins exit / help (FR-10, FR-11) -----------------------------------
t TC-31 FR-10 "exit N returns status N"                         'exit 7' '' 7
t TC-32 FR-10 "exit stops further commands"                     'echo a; exit 3; echo b' 'a' 3
t TC-33 FR-10 "exit with non-numeric argument -> status 2"      'exit abc' '' 2 'numeric argument required'
out="$(cd "$W" && "$MYSH" -c 'help' 2>&1)"; rc=$?
if [ $rc -eq 0 ] && echo "$out" | grep -q 'cd \[dir' && echo "$out" | grep -q 'exit \[status\]' && echo "$out" | grep -q 'pwd'; then
    record TC-34 FR-11 0 "help lists the built-in commands"
else record TC-34 FR-11 1 "help lists the built-in commands" "output: $out"; fi

# ---- Sequencing, quoting, comments, syntax errors (FR-03, FR-04, FR-19) ---
t TC-35 FR-19 "; runs commands in order"                        'echo a; echo b; echo c' $'a\nb\nc'
t TC-37 FR-03 "double quotes preserve inner spaces"             'echo "a   b"' 'a   b'
t TC-39 FR-03 "backslash escapes a space"                       'echo a\ b' 'a b'
t TC-40 FR-03 "comment is ignored"                              'echo hi # comment' 'hi'
t TC-41 FR-04 "unterminated quote -> syntax error, status 2"    'echo "abc' '' 2 'unterminated double quote'
t TC-42 FR-04 "leading | is a syntax error"                     '| ls' '' 2 'syntax error'
t TC-43 FR-04 "trailing | is a syntax error"                    'ls |' '' 2 'syntax error'
t TC-44 FR-04 "redirection without file name"                   'cat <' '' 2 'missing file name'
t TC-45 FR-04 "&& is reported as unsupported"                   'echo a && echo b' '' 2 "'&&' is not supported"
t TC-46 FR-04 "syntax error discards rest of line"              'echo before; echo "oops; echo after' 'before' 2 'unterminated'
t TC-47 FR-01 "blank / whitespace-only input does nothing"      '     ' '' 0
t TC-73 FR-04 "|| is reported as unsupported"                   'false || echo b' '' 2 "'||' is not supported"

# ---- PATH and paths (FR-05) ---------------------------------------------------
t TC-48 FR-05 "PATH lookup finds a user-added directory"        "export PATH=$W/bin:\$PATH; hello_tool" 'tool-ran'
t TC-49 FR-05 "relative path with / bypasses PATH"              './bin/hello_tool' 'tool-ran'

# ---- Background execution (FR-20) -------------------------------------------
start=$(date +%s%N)
# NOTE: output goes to a file, not $(...): a background child would otherwise keep
# the command-substitution pipe open and make the *test harness* wait for it.
(cd "$W" && "$MYSH" -c 'sleep 2 & echo started' >"$W/.bgout" 2>/dev/null)
end=$(date +%s%N); out="$(cat "$W/.bgout")"; ms=$(( (end-start)/1000000 ))
if [ "$out" = "started" ] && [ "$ms" -lt 1500 ]; then
    record TC-36 FR-20 0 "'sleep 2 &' returns immediately (took ${ms} ms)"
else record TC-36 FR-20 1 "'sleep 2 &' returns immediately" "out=[$out] took ${ms} ms"; fi

start=$(date +%s%N)
(cd "$W" && "$MYSH" -c 'sleep 1 | sleep 1 & echo bg-pipeline' >"$W/.bgout" 2>/dev/null)
end=$(date +%s%N); out="$(cat "$W/.bgout")"; ms=$(( (end-start)/1000000 ))
if [ "$out" = "bg-pipeline" ] && [ "$ms" -lt 800 ]; then
    record TC-74 FR-20 0 "background pipeline does not block the shell (took ${ms} ms)"
else record TC-74 FR-20 1 "background pipeline does not block the shell" "out=[$out] took ${ms} ms"; fi

out="$(cd "$W" && "$MYSH" -c 'echo bgdata > bg.txt & sleep 0.5; cat bg.txt' 2>/dev/null)"
if [ "$out" = "bgdata" ]; then record TC-75 FR-20 0 "background command with redirection completes its work"
else record TC-75 FR-20 1 "background command with redirection completes its work" "out=[$out]"; fi

# ---- Input sources (FR-02, FR-22) ---------------------------------------------
printf 'echo line1\necho line2\n' > "$W/script.mysh"
out="$(cd "$W" && "$MYSH" script.mysh 2>&1)"
[ "$out" = $'line1\nline2' ] && record TC-50 FR-02 0 "script file argument is executed" \
    || record TC-50 FR-02 1 "script file argument is executed" "out=[$out]"

out="$(printf 'echo a\necho b\n' | (cd "$W" && "$MYSH") 2>&1)"
[ "$out" = $'a\nb' ] && record TC-51 FR-02 0 "commands can be piped to the shell on stdin (no prompt)" \
    || record TC-51 FR-02 1 "commands can be piped to the shell on stdin (no prompt)" "out=[$out]"

printf 'false\n' | (cd "$W" && "$MYSH") >/dev/null 2>&1; rc=$?
[ $rc -eq 1 ] && record TC-52 FR-22 0 "EOF on stdin ends the shell with the last command's status" \
    || record TC-52 FR-22 1 "EOF on stdin ends the shell with the last command's status" "rc=$rc"

printf 'echo first\nexit 5\necho never\n' > "$W/exit.mysh"
out="$(cd "$W" && "$MYSH" exit.mysh 2>&1)"; rc=$?
[ "$out" = "first" ] && [ $rc -eq 5 ] && record TC-53 FR-10 0 "exit inside a script stops the script" \
    || record TC-53 FR-10 1 "exit inside a script stops the script" "out=[$out] rc=$rc"

"$MYSH" -c >/dev/null 2>&1; rc=$?
[ $rc -eq 2 ] && record TC-62 FR-02 0 "'-c' without an argument -> usage error (status 2)" \
    || record TC-62 FR-02 1 "'-c' without an argument -> usage error (status 2)" "rc=$rc"

"$MYSH" /no/such/script >/dev/null 2>&1; rc=$?
[ $rc -eq 127 ] && record TC-63 FR-02 0 "missing script file -> status 127" \
    || record TC-63 FR-02 1 "missing script file -> status 127" "rc=$rc"

out="$("$MYSH" --version 2>&1)"
case "$out" in mysh*) record TC-76 FR-02 0 "--version prints the version";; *) record TC-76 FR-02 1 "--version prints the version" "out=[$out]";; esac

# ---- Robustness (NFR-02) --------------------------------------------------------
args="$(seq 1 2000 | tr '\n' ' ')"
n="$(cd "$W" && "$MYSH" -c "echo $args" | wc -w)"
[ "$n" -eq 2000 ] && record TC-54 NFR-02 0 "command with 2000 arguments" \
    || record TC-54 NFR-02 1 "command with 2000 arguments" "counted $n words"

big="$(head -c 100000 /dev/zero | tr '\0' a)"
n="$(cd "$W" && "$MYSH" -c "echo $big" | wc -c)"
[ "$n" -eq 100001 ] && record TC-55 NFR-02 0 "single 100000-character argument" \
    || record TC-55 NFR-02 1 "single 100000-character argument" "counted $n bytes"

# many sequential commands must not leak descriptors or zombies
cmds="$(for i in $(seq 1 300); do printf 'true | true; '; done)"
out="$(cd "$W" && "$MYSH" -c "$cmds echo survived" 2>&1)"
[ "$out" = "survived" ] && record TC-77 NFR-02 0 "300 consecutive pipelines (no fd/process leak)" \
    || record TC-77 NFR-02 1 "300 consecutive pipelines (no fd/process leak)" "out=[$out]"


# ======================= SECURITY TESTS (SC-xx) =================================
cp "$ROOT/tests/fdcheck.py" "$W/fdcheck.py"
t SC-01 SR-01 "metacharacters inside quotes are passed literally; no injection" \
  'echo "a; echo injected | cat > pwned"; ls pwned; echo ls-status=$?' $'a; echo injected | cat > pwned\nls-status=2' 0 'No such file'
t SC-02 SR-02 "operators inside a variable value are not re-interpreted" \
  'X="a; echo pwned"; echo $X' 'a; echo pwned'
(cd "$W" && "$MYSH" -c "echo hi > 'weird;name|x'" 2>/dev/null); rc=$?
meta SC-03 "echo hi > 'weird;name|x'" "exit status 0; one file named exactly weird;name|x containing hi"
if [ $rc -eq 0 ] && [ "$(cat "$W/weird;name|x" 2>/dev/null)" = "hi" ]; then record SC-03 SR-01 0 "file names containing metacharacters are used literally"
else record SC-03 SR-01 1 "file names containing metacharacters are used literally" "rc=$rc"; fi
meta SC-04 "grep -E '(system|popen)\\s*\\(' src/*.c  and  grep for exec of /bin/sh" "no matches (user text is never handed to another shell)"
if ! grep -nE '\b(system|popen)[[:space:]]*\(' "$ROOT"/src/*.c >/dev/null && ! grep -nE '"/bin/sh"|"-c"[[:space:]]*,' "$ROOT"/src/executor.c "$ROOT"/src/builtins.c >/dev/null; then
    record SC-04 SR-01 0 "source contains no system()/popen()/sh -c invocation"
else record SC-04 SR-01 1 "source contains no system()/popen()/sh -c invocation" "forbidden call found"; fi
meta SC-05 "grep for setuid/setgid/seteuid/setreuid in src/; mysh -c 'id -u'" "no matches; child uid equals the invoking user's uid"
mine="$(id -u)"; theirs="$(cd "$W" && "$MYSH" -c 'id -u' 2>/dev/null)"
if ! grep -nE '\bset(e|re|res)?[ug]id[[:space:]]*\(' "$ROOT"/src/*.c >/dev/null && [ "$mine" = "$theirs" ]; then
    record SC-05 SR-03 0 "shell never changes uid/gid; children run as the invoking user (uid $mine)"
else record SC-05 SR-03 1 "shell never changes uid/gid; children run as the invoking user" "uid mine=$mine child=$theirs"; fi
H="$(mktemp -d)"; C="$(mktemp -d)"
printf 'echo a | cat\ncd /\npwd\nexport Q=1\nnosuchcmd\necho x > /dev/null\n' | (cd "$C" && HOME="$H" "$MYSH" >/dev/null 2>&1)
left="$(find "$H" "$C" -mindepth 1 | wc -l)"; rm -rf "$H" "$C"
meta SC-06 "session of 6 commands (pipe, cd, export, error, redirect to /dev/null) with HOME and cwd empty" "no file created in HOME or cwd (no history, no log)"
[ "$left" -eq 0 ] && record SC-06 SR-04 0 "shell writes no history/log/state files of its own" || record SC-06 SR-04 1 "shell writes no history/log/state files of its own" "$left stray files"
( umask 077; cd "$W" && "$MYSH" -c 'echo x > m077.txt' 2>/dev/null ); ( umask 022; cd "$W" && "$MYSH" -c 'echo x > m022.txt' 2>/dev/null ); ( umask 000; cd "$W" && "$MYSH" -c 'echo x > m000.txt >> m000.txt' 2>/dev/null )
a="$(stat -c %a "$W/m077.txt")"; b="$(stat -c %a "$W/m022.txt")"; c="$(stat -c %a "$W/m000.txt")"
meta SC-07 "echo x > f   under umask 077 / 022 / 000" "file modes 600 / 644 / 644 (never more permissive than 0644)"
[ "$a/$b/$c" = "600/644/644" ] && record SC-07 SR-05 0 "created files are never more permissive than 0644 and honour the umask" || record SC-07 SR-05 1 "created files are never more permissive than 0644 and honour the umask" "modes $a/$b/$c"
t SC-08 SR-07 "invalid variable names are rejected and the environment is unchanged" \
  'export "a-b=1"; echo $?; env | grep -c a-b' $'1\n0' 1 'not a valid identifier'
cmds="$(for i in $(seq 1 300); do printf 'true | true; '; done)"
out="$(cd "$W" && "$MYSH" -c "$cmds python3 fdcheck.py" 2>/dev/null)"
meta SC-09 "300 x 'true | true' then python3 fdcheck.py (lists inherited descriptors >= 3)" "[]"
[ "$out" = "[]" ] && record SC-09 SR-08 0 "executed programs inherit no descriptors beyond 0,1,2 after 300 pipelines" || record SC-09 SR-08 1 "executed programs inherit no descriptors beyond 0,1,2 after 300 pipelines" "got $out"
printf 'python3 fdcheck.py\n' > "$W/fd.mysh"
out="$(cd "$W" && "$MYSH" fd.mysh 2>/dev/null)"
meta SC-10 "mysh fd.mysh   (script runs python3 fdcheck.py)" "[]  (the script file descriptor is close-on-exec)"
[ "$out" = "[]" ] && record SC-10 SR-08 0 "script file descriptor is not inherited by executed programs" || record SC-10 SR-08 1 "script file descriptor is not inherited by executed programs" "got $out"
(cd "$W" && printf 'SECRET\n' | "$MYSH" -c 'cat & sleep 0.5' >"$W/.bgout" 2>/dev/null)
meta SC-11 "printf 'SECRET' | mysh -c 'cat & sleep 0.5'" "no output: the background cat read /dev/null, not the shell's stdin"
[ ! -s "$W/.bgout" ] && record SC-11 SR-10 0 "background jobs cannot read the shell's standard input" || record SC-11 SR-10 1 "background jobs cannot read the shell's standard input" "leaked: $(cat "$W/.bgout")"
# SC-12 / SC-13 (fuzzing) are produced by 'make fuzz' -> tests/results_fuzz.txt

# ======================= NON-FUNCTIONAL TESTS (NF-xx) ===========================
start=$(date +%s%N)
(cd "$W" && "$MYSH" -c 'sleep 2 & echo started' >"$W/.bgout" 2>/dev/null)
end=$(date +%s%N); ms=$(( (end-start)/1000000 ))
meta NF-01 "sleep 2 & echo started" "control returns in <= 500 ms although the job runs 2 s"
[ "$ms" -le 500 ] && record NF-01 NFR-01 0 "background start returns in <= 500 ms (measured ${ms} ms)" || record NF-01 NFR-01 1 "background start returns in <= 500 ms" "took ${ms} ms"
cmds="$(for i in $(seq 1 1000); do printf 'true; '; done)"
start=$(date +%s%N); (cd "$W" && "$MYSH" -c "$cmds" >/dev/null 2>&1); end=$(date +%s%N); ms=$(( (end-start)/1000000 ))
meta NF-02 "1000 x 'true' (fork+exec) in one -c string" "total <= 5000 ms (mean <= 5 ms per external command)"
[ "$ms" -le 5000 ] && record NF-02 NFR-01 0 "1000 external commands in <= 5 s (measured ${ms} ms, mean $((ms*1000/1000)) us)" || record NF-02 NFR-01 1 "1000 external commands in <= 5 s" "took ${ms} ms"
cmds="$(for i in $(seq 1 1000); do printf 'pwd > /dev/null; '; done)"
start=$(date +%s%N); (cd "$W" && "$MYSH" -c "$cmds" >/dev/null 2>&1); end=$(date +%s%N); ms=$(( (end-start)/1000000 ))
meta NF-03 "1000 x 'pwd > /dev/null' (built-in, no process)" "total <= 1000 ms"
[ "$ms" -le 1000 ] && record NF-03 NFR-01 0 "1000 built-in commands in <= 1 s (measured ${ms} ms)" || record NF-03 NFR-01 1 "1000 built-in commands in <= 1 s" "took ${ms} ms"
badmsgs=0; total=0
for c in 'invalidcommand' 'cd /nonexistent' 'cat < /nonexistent' 'echo hi > /nonexistent/x' 'echo "oops' '| ls' 'export 1x=2' 'exit abc' './noexec.sh' 'cd a b' 'echo a && b' './nothere'; do
  e="$(cd "$W" && "$MYSH" -c "$c" 2>&1 >/dev/null)"
  while IFS= read -r l; do total=$((total+1)); case "$l" in "mysh: "?*) ;; *) badmsgs=$((badmsgs+1));; esac; done <<< "$e"
done
meta NF-04 "12 different error scenarios (bad command, bad cd, bad redirect, syntax errors, bad export/exit)" "every stderr line starts with 'mysh: ' followed by a reason"
[ "$badmsgs" -eq 0 ] && [ "$total" -ge 12 ] && record NF-04 NFR-03 0 "all $total diagnostic lines of 12 error scenarios use the 'mysh: <reason>' format" || record NF-04 NFR-03 1 "diagnostics use the 'mysh: <reason>' format" "$badmsgs of $total lines malformed"
ok=0
for f in "$ROOT"/src/*.c; do gcc -std=c11 -D_POSIX_C_SOURCE=200809L -D_DEFAULT_SOURCE -Wall -Wextra -Wpedantic -Werror -fsyntax-only "$f" 2>/dev/null || ok=1; done
meta NF-05 "gcc -std=c11 -Wall -Wextra -Wpedantic -Werror -fsyntax-only src/*.c" "no warnings, no errors"
[ $ok -eq 0 ] && record NF-05 NFR-04 0 "all 6 source files compile with 0 warnings under -Wall -Wextra -Wpedantic -Werror" || record NF-05 NFR-04 1 "all source files compile with 0 warnings under -Werror" "warning or error"
ok=0
for f in "$ROOT"/src/*.c; do gcc -std=c99 -D_POSIX_C_SOURCE=200809L -D_DEFAULT_SOURCE -Wall -Wextra -Werror -fsyntax-only "$f" 2>/dev/null || ok=1; done
meta NF-06 "gcc -std=c99 -fsyntax-only src/*.c   (C99 plus POSIX.1-2008 only)" "compiles; no compiler-specific extensions needed beyond POSIX"
[ $ok -eq 0 ] && record NF-06 NFR-05 0 "sources also compile as C99 + POSIX.1-2008 (no GNU-only language extensions)" || record NF-06 NFR-05 1 "sources also compile as C99 + POSIX.1-2008" "failed"
out="$(printf 'nosuchcmd\ncd /nonexistent\ncat < /nonexistent\necho "oops\n| ls\nexport 1x=2\n./noexec.sh\necho a && b\ncd a b\ncat < /nonexistent | cat\necho alive\n' | (cd "$W" && "$MYSH" 2>/dev/null))"
meta NF-07 "10 faulty lines (bad command, cd, redirect, syntax, export, permissions, && ...) then 'echo alive'" "only 'alive' is printed: the shell survived every error"
[ "$out" = "alive" ] && record NF-07 NFR-09 0 "shell survives 10 consecutive faulty lines and still executes the next command" || record NF-07 NFR-09 1 "shell survives 10 consecutive faulty lines and still executes the next command" "out=[$out]"
out="$(cd "$W" && "$MYSH" -c 'help' 2>&1)"; lines="$(printf '%s\n' "$out" | wc -l)"; widest="$(printf '%s\n' "$out" | awk '{ if (length($0)>m) m=length($0) } END { print m }')"
meta NF-08 "help" "at most 25 lines, no line longer than 80 characters, lists all 7 built-ins"
n7=0; for b in cd pwd exit help export unset env; do printf '%s\n' "$out" | grep -qE "^  $b( |\$)" && n7=$((n7+1)); done
[ "$lines" -le 25 ] && [ "$widest" -le 80 ] && [ "$n7" -eq 7 ] && record NF-08 NFR-03 0 "help fits one screen (${lines} lines, widest ${widest} columns) and lists all 7 built-ins" || record NF-08 NFR-03 1 "help fits one screen and lists all 7 built-ins" "lines=$lines widest=$widest builtins=$n7"

# ---- System test: full demonstration script ---------------------------------
if [ -f "$W/demo.mysh" ]; then
    out="$(cd "$W" && "$MYSH" demo.mysh 2>&1)"; rc=$?
    ok=0
    for needle in "Hello, Shell!" "Welcome Student" "first line" "second line" "command not found" "status was 127" "background job started"; do
        echo "$out" | grep -qF "$needle" || { ok=1; why="missing [$needle]"; }
    done
    [ $rc -eq 0 ] || { ok=1; why="rc=$rc"; }
    record ST-10 "FR-01..FR-22" $ok "demo/demo.mysh runs end to end and produces the documented output" "$why"
else
    record ST-10 "FR-01..FR-22" 1 "demo/demo.mysh runs end to end" "demo script missing"
fi

sk=""; [ "$skipped" -gt 0 ] && sk=", $skipped skipped (not implemented yet)"
echo "FUNCTIONAL SUMMARY: $((pass+fail)) run, $pass passed, $fail failed$sk"
echo "FUNCTIONAL SUMMARY: $((pass+fail)) run, $pass passed, $fail failed$sk" >> "$RESULTS"
[ $fail -eq 0 ]
