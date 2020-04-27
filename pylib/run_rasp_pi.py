#!/usr/bin/env python3

# Python module to run programs natively.

# Copyright (C) 2019 Clemson University
#
# Contributor: Ola Jeppsson <ola.jeppsson@gmail.com>
#
# This file is part of Embench.

# SPDX-License-Identifier: GPL-3.0-or-later

"""
Embench module to run benchmark programs.

This version is suitable for running programs natively.
"""

__all__ = [
    'get_target_args',
    'build_benchmark_cmd',
    'decode_results',
]

import argparse
import re

from embench_core import log


def get_target_args(remnant):
    """Parse left over arguments"""
    parser = argparse.ArgumentParser(description='Get target specific args')

    # No target arguments
    return parser.parse_args(remnant)


def build_benchmark_cmd(bench, args):
    """Construct the command to run the benchmark.  "args" is a
       namespace with target specific arguments"""

    # alter clock_gettime() to get more accurate results
    # edited in config/aarch64/raspberry-pi/boardsupport.c
    # use taskset to bind a certain core
    return ['sh', '-c', 'taskset -c 1 ./' + bench + '; echo RET=$?']


def decode_results(stdout_str, stderr_str):
    """Extract the results from the output string of the run. Return the
       elapsed time in milliseconds or zero if the run failed."""
    # See above in build_benchmark_cmd how we record the return value and
    # execution time. Return code is in standard output. Execution time is in
    # standard error.

    # Match "RET=rc"
    rcstr = re.search('^RET=(\d+)', stdout_str, re.S)
    if not rcstr:
        log.debug('Warning: Failed to find return code')
        return 0.0

    # Match "real s.mm?m?"
    time = re.search('^time (\d+)ns', stderr_str, re.S)
    if time:
        ms_elapsed = int(time.group(1)) / 1000000
        # Return value cannot be zero (will be interpreted as error)
        return max(float(ms_elapsed), 0.001)

    # We must have failed to find a time
    log.debug('Warning: Failed to find timing')
    return 0.0
