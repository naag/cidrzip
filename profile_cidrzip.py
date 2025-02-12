#!/usr/bin/env python3

import cProfile
import pstats
from pstats import SortKey
import os
from cidrzip import CIDRZip

def profile_aws_cidrs():
    """Profile CIDRZip with AWS CIDRs example file."""
    zipper = CIDRZip()

    # Read AWS CIDRs
    cidrs = zipper.read_from_file("examples/aws_cidrs.txt")

    # Create a large dataset by duplicating the CIDRs to simulate 1000+ entries
    large_cidrs = cidrs * (1000 // len(cidrs) + 1)
    print(f"Testing with {len(large_cidrs)} CIDRs...")

    # Test cases with different modes
    test_cases = [
        (500, 'optimal'),
        (500, 'greedy'),
        (500, 'windowed'),  # default window_size=50
        (500, 'windowed', 10),  # smaller window
        (776, 'optimal'),
        (776, 'greedy'),
    ]

    for case in test_cases:
        n = case[0]
        mode = case[1]
        window_size = case[2] if len(case) > 2 else 50

        print(f"\nProfiling with n_groups={n}, mode={mode}" + (f", window={window_size}" if mode == 'windowed' else ""))
        profiler = cProfile.Profile()
        profiler.enable()

        if mode == 'windowed':
            result = zipper.group(large_cidrs, n, mode=mode, window_size=window_size)
        else:
            result = zipper.group(large_cidrs, n, mode=mode)

        profiler.disable()
        stats = pstats.Stats(profiler).sort_stats(SortKey.TIME)
        stats.print_stats(20)  # Show top 20 time-consuming functions
        print(f"Resulted in {len(result)} groups")

if __name__ == "__main__":
    profile_aws_cidrs()