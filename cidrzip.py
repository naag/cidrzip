#!/usr/bin/env python3
# Copyright (c) 2025 Peter Bücker
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import ipaddress
from typing import List, Optional, Tuple
import sys

class CIDRZip:
    """A class for efficiently compressing and merging CIDR blocks."""

    @staticmethod
    def smallest_covering_network(start: ipaddress.IPv4Address, end: ipaddress.IPv4Address) -> ipaddress.IPv4Network:
        """
        Given two IPv4Addresses start and end, returns the smallest IPv4Network (with strict=False)
        that covers the entire range [start, end].
        """
        start_int = int(start)
        end_int = int(end)
        diff = start_int ^ end_int
        prefix = 32 if diff == 0 else 32 - diff.bit_length()
        return ipaddress.ip_network((start, prefix), strict=False)

    def group(self, cidrs: List[str], n: int) -> List[str]:
        """
        Group a list of CIDR strings into at most n larger, non-overlapping CIDR ranges.

        Args:
            cidrs: List of CIDR strings to group
            n: Maximum number of groups to create

        Returns:
            List of CIDR strings representing the grouped networks

        If the collapsed (exact) set of CIDRs is already ≤ n, return it.
        Otherwise, merge contiguous blocks (possibly adding extra addresses)
        so that the output is exactly n CIDR ranges while minimizing extra coverage.
        """
        if not cidrs:
            return []

        # Parse the CIDR strings into IPv4Network objects
        nets = [ipaddress.ip_network(c) for c in cidrs]

        # Collapse (merge) any overlapping or immediately adjacent networks
        collapsed = list(ipaddress.collapse_addresses(nets))
        # Sort by network address (as integers)
        collapsed.sort(key=lambda net: int(net.network_address))
        m = len(collapsed)

        # If we already have n or fewer groups, we are done
        if n >= m:
            return [str(net) for net in collapsed]

        # Precompute a prefix sum of the sizes for quick segment size computation
        sizes = [net.num_addresses for net in collapsed]
        prefix_sum = [0] * (m + 1)
        for i in range(m):
            prefix_sum[i+1] = prefix_sum[i] + sizes[i]

        # Precompute merge costs and merged networks for all possible segments
        cost = [[0] * m for _ in range(m)]
        merged_net = [[None] * m for _ in range(m)]
        for i in range(m):
            for j in range(i, m):
                start = collapsed[i].network_address
                end = collapsed[j].broadcast_address
                merged = self.smallest_covering_network(start, end)
                merged_net[i][j] = merged
                total = prefix_sum[j+1] - prefix_sum[i]
                cost[i][j] = merged.num_addresses - total

        # Dynamic programming to find optimal segmentation
        dp = [[float('inf')] * (n+1) for _ in range(m+1)]
        partition = [[-1] * (n+1) for _ in range(m+1)]

        dp[m][0] = 0  # Base case: no networks left, 0 segments needed

        # Fill the DP table
        for i in range(m - 1, -1, -1):
            for s in range(1, n+1):
                for j in range(i, m - s + 1):
                    current = cost[i][j] + dp[j+1][s-1]
                    if current < dp[i][s]:
                        dp[i][s] = current
                        partition[i][s] = j

        # Reconstruct the optimal segmentation
        segments = []
        i, segs_left = 0, n
        while segs_left:
            j = partition[i][segs_left]
            segments.append((i, j))
            i = j + 1
            segs_left -= 1

        # Convert segments to CIDR strings
        return [str(merged_net[i][j]) for i, j in segments]

    @staticmethod
    def read_from_file(filepath: str) -> List[str]:
        """
        Read CIDRs from a file, one per line.
        Empty lines and lines starting with # are ignored.

        Args:
            filepath: Path to the file containing CIDR ranges

        Returns:
            List of CIDR strings from the file
        """
        with open(filepath, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def group_cidrs(cidrs: List[str], n: int) -> List[str]:
    """
    Legacy function for backward compatibility.
    Use CIDRZip().group() for new code.
    """
    return CIDRZip().group(cidrs, n)

def read_cidrs_from_file(filepath: str) -> List[str]:
    """
    Legacy function for backward compatibility.
    Use CIDRZip.read_from_file() for new code.
    """
    return CIDRZip.read_from_file(filepath)

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print("Error: Please provide an input file path")
        sys.exit(1)

    input_file = sys.argv[1]
    zipper = CIDRZip()

    try:
        sample_cidrs = zipper.read_from_file(input_file)
        # Group into at most 10 CIDRs
        grouped = zipper.group(sample_cidrs, 10)
        print("Grouped CIDRs:")
        for cidr in grouped:
            print(cidr)
    except FileNotFoundError:
        print(f"Error: Could not find file {input_file}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

