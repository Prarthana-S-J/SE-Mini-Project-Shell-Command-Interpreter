# Simple Shell (mysh) - build system
CC      ?= gcc
AR      ?= ar
CFLAGS  ?= -std=c11 -Wall -Wextra -Wpedantic -O2 -g
CPPFLAGS += -D_POSIX_C_SOURCE=200809L -D_DEFAULT_SOURCE

SRC_DIR   := src
BUILD_DIR := build
TARGET    := mysh
PARSER_LIB := $(BUILD_DIR)/libmysh_parser.a

SRCS := $(filter-out $(SRC_DIR)/main.c,$(wildcard $(SRC_DIR)/*.c))
OBJS := $(SRCS:$(SRC_DIR)/%.c=$(BUILD_DIR)/%.o)
MAIN := $(BUILD_DIR)/main.o

.PHONY: all clean test unit-test sanitize fuzz run

all: $(TARGET) $(PARSER_LIB)

$(TARGET): $(OBJS) $(MAIN)
	$(CC) $(CFLAGS) -o $@ $^

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c $(wildcard $(SRC_DIR)/*.h) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c -o $@ $<

$(BUILD_DIR):
	mkdir -p $@

$(BUILD_DIR)/parser_api.o: parser.c parser.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c -o $@ $<

$(PARSER_LIB): $(BUILD_DIR)/parser_api.o
	$(AR) rcs $@ $^

# Parser/utility unit tests (Member 4)
$(BUILD_DIR)/test_parser: tests/test_parser.c parser.c parser.h $(OBJS) | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) -I$(SRC_DIR) -o $@ tests/test_parser.c parser.c $(OBJS)

ifneq ($(wildcard $(SRC_DIR)/parser.c),)
unit-test: $(BUILD_DIR)/test_parser
	./$(BUILD_DIR)/test_parser > tests/results_unit.txt; rc=$$?; cat tests/results_unit.txt; exit $$rc
else
unit-test:
	@echo "parser not implemented yet - no unit tests to run"
endif

# Functional / integration / system tests (need ./mysh)
test: all unit-test
	bash tests/run_tests.sh
	python3 tests/interactive_test.py
	$(MAKE) fuzz

# Build with AddressSanitizer + UBSan and rerun the tests against that binary
sanitize:
	$(MAKE) clean
	$(MAKE) CFLAGS="-std=c11 -Wall -Wextra -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer" all unit-test
	ASAN_OPTIONS=detect_leaks=1 bash tests/run_tests.sh

# Security validation: random-input fuzzing under AddressSanitizer + UBSan (Member 4)
ASAN_FLAGS := -std=c11 -Wall -Wextra -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer
fuzz:
	mkdir -p build-asan
	$(CC) $(CPPFLAGS) $(ASAN_FLAGS) -Isrc -o build-asan/fuzz_parser tests/fuzz_parser.c $(SRCS)
	$(CC) $(CPPFLAGS) $(ASAN_FLAGS) -o build-asan/mysh $(SRC_DIR)/*.c
	( ./build-asan/fuzz_parser || echo "SC-12 SR-06 FAIL parser fuzz aborted (sanitizer or invariant failure)" ) > tests/results_fuzz.txt
	MYSH=$(CURDIR)/build-asan/mysh python3 tests/fuzz_shell.py >> tests/results_fuzz.txt; true
	cat tests/results_fuzz.txt

run: all
	./$(TARGET)

clean:
	rm -rf $(BUILD_DIR) build-asan $(TARGET)
