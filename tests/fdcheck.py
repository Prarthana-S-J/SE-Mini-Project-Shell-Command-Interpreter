#!/usr/bin/env python3
# Prints the list of open file descriptors >= 3 of this process (used by SC-09 / SC-10).
import os
print([f for f in range(3, 256) if os.path.exists('/proc/self/fd/%d' % f)])
