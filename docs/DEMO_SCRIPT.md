# Demonstration Script

Run the shell with `make && ./mysh`. Follow the steps in order in one interactive session (about 5 minutes).

### Step 1

**Command:** `./mysh`  
**Expected behavior:** A prompt of the form mysh:/path$ appears.  
**What this demonstrates:** Interactive shell start (FR-01).

### Step 2

**Command:** `pwd`  
**Expected behavior:** Prints the current directory.  
**What this demonstrates:** Built-in pwd (FR-09).

### Step 3

**Command:** `echo Hello, Shell!`  
**Expected behavior:** Prints Hello, Shell!  
**What this demonstrates:** External command via fork/execvp and PATH search (FR-05, FR-06).

### Step 4

**Command:** `help`  
**Expected behavior:** Lists cd, pwd, exit, help, export, unset, env and the operators.  
**What this demonstrates:** Built-in help (FR-11).

### Step 5

**Command:** `mkdir demo_work`  
**Expected behavior:** No output.  
**What this demonstrates:** Another external command.

### Step 6

**Command:** `cd demo_work`  
**Expected behavior:** No output; then `pwd` shows .../demo_work.  
**What this demonstrates:** Built-in cd changes the shell's own directory (FR-08).

### Step 7

**Command:** `export NAME=Student`  
**Expected behavior:** No output.  
**What this demonstrates:** Environment variable (FR-12).

### Step 8

**Command:** `echo Welcome $NAME`  
**Expected behavior:** Prints Welcome Student  
**What this demonstrates:** Variable expansion (FR-13).

### Step 9

**Command:** `echo first line > notes.txt`  
**Expected behavior:** No output; file notes.txt is created.  
**What this demonstrates:** Output redirection (FR-14).

### Step 10

**Command:** `echo second line >> notes.txt`  
**Expected behavior:** No output; line appended.  
**What this demonstrates:** Append redirection (FR-15).

### Step 11

**Command:** `cat < notes.txt`  
**Expected behavior:** Prints both lines.  
**What this demonstrates:** Input redirection (FR-16).

### Step 12

**Command:** `cat notes.txt | grep second`  
**Expected behavior:** Prints only: second line  
**What this demonstrates:** Pipe between two processes (FR-18).

### Step 13

**Command:** `ls | sort | head -n 3`  
**Expected behavior:** Prints notes.txt  
**What this demonstrates:** Three-stage pipeline (FR-18).

### Step 14

**Command:** `sleep 5 &`  
**Expected behavior:** Prints [1] <pid> and the prompt returns at once; later `[1]+  Done   sleep 5` appears before a prompt.  
**What this demonstrates:** Background execution and job reaping (FR-20).

### Step 15

**Command:** `sleep 30   then press Ctrl+C`  
**Expected behavior:** Sleep is killed, a newline is printed, prompt returns; `echo $?` prints 130.  
**What this demonstrates:** Signal handling; shell survives (FR-21, FR-06).

### Step 16

**Command:** `invalidcommand`  
**Expected behavior:** mysh: invalidcommand: command not found; `echo $?` prints 127.  
**What this demonstrates:** Invalid-command handling (FR-07).

### Step 17

**Command:** `cd nosuchdir`  
**Expected behavior:** mysh: cd: nosuchdir: No such file or directory  
**What this demonstrates:** Built-in error handling (FR-08).

### Step 18

**Command:** `cat < missing.txt`  
**Expected behavior:** mysh: missing.txt: No such file or directory  
**What this demonstrates:** Redirection error (FR-17).

### Step 19

**Command:** `echo one; echo two`  
**Expected behavior:** one / two on separate lines.  
**What this demonstrates:** Sequencing with ; (FR-19).

### Step 20

**Command:** `exit   (or press Ctrl+D)`  
**Expected behavior:** Shell terminates.  
**What this demonstrates:** Graceful termination (FR-10, FR-22).

## Scripted (non-interactive) run

`demo/demo.mysh` runs a subset of the steps without a terminal: `./mysh demo/demo.mysh`. This is the captured result of an actual run on 2026-10-03 (stdout, then stderr):

```
<dir>
Hello, Shell!
<dir>/demo_work
Welcome Student
first line
second line
second line
notes.txt
background job started
status was 127
```

```
mysh: invalidcommand: command not found
mysh: cd: nosuchdir: No such file or directory
```

(In non-interactive mode no prompt or `[1] pid` job banner is printed.) The same script is executed as system test ST-10.
