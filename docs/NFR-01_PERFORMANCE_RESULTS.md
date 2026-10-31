# NFR-01: Performance Test Results

## 1. Objective

Verify that the Simple Shell Command Interpreter satisfies the performance requirements defined in NFR-01 of the Software Requirements Specification (SRS).

## 2. Test Environment

- Build type: Normal optimized build
- Compiler flags: `-O2 -g`
- Build command: `make clean && make`
- Test command: `bash tests/run_tests.sh`
- Test framework: Project functional, integration and system test suite

## 3. Performance Requirements and Results

| Test ID | Test Description | Required Limit | Measured Time | Result |
|---|---|---:|---:|---|
| NF-01 | Background command start returns without waiting for job completion | <= 500 ms | 64 ms | PASS |
| NF-02 | Execute 1000 consecutive external `true` commands | <= 5000 ms | 2207 ms | PASS |
| NF-03 | Execute 1000 consecutive built-in `pwd` commands | <= 1000 ms | 52 ms | PASS |

## 4. Observations

- NF-01 returned control in 64 ms, within the specified 500 ms limit.
- NF-02 completed 1000 external commands in 2207 ms, averaging approximately 2.207 ms per command.
- NF-03 completed 1000 built-in commands in 52 ms, within the specified 1000 ms limit.
- All three NFR-01 performance tests passed.

## 5. Conclusion

The measured results satisfy all three performance limits specified in NFR-01 under the tested environment and build configuration.

**Overall Result: PASS (3/3 performance tests).**
