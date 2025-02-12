#!/usr/bin/env python3

import ipaddress
from typing import List
import sys

def smallest_covering_network(start: ipaddress.IPv4Address, end: ipaddress.IPv4Address) -> ipaddress.IPv4Network:
    """
    Given two IPv4Addresses start and end, returns the smallest IPv4Network (with strict=False)
    that covers the entire range [start, end].
    """
    start_int = int(start)
    end_int = int(end)
    diff = start_int ^ end_int
    prefix = 32 if diff == 0 else 32 - diff.bit_length()
    # The constructor with strict=False will adjust the network address if necessary.
    return ipaddress.ip_network((start, prefix), strict=False)

def group_cidrs(cidrs: List[str], n: int) -> List[str]:
    """
    Group a list of CIDR strings into at most n larger, non-overlapping CIDR ranges.

    If the collapsed (exact) set of CIDRs is already ≤ n, return it.
    Otherwise, merge contiguous blocks (possibly adding extra addresses)
    so that the output is exactly n CIDR ranges while minimizing extra coverage.
    """
    if not cidrs:
        return []

    # Parse the CIDR strings into IPv4Network objects.
    nets = [ipaddress.ip_network(c) for c in cidrs]

    # Collapse (merge) any overlapping or immediately adjacent networks.
    collapsed = list(ipaddress.collapse_addresses(nets))
    # Sort by network address (as integers)
    collapsed.sort(key=lambda net: int(net.network_address))
    m = len(collapsed)

    # If we already have n or fewer groups, we are done.
    if n >= m:
        return [str(net) for net in collapsed]

    # We'll now treat the m networks as items that must be partitioned (in order) into n segments.
    # For each contiguous segment we will cover it with the smallest possible network.
    # The "cost" (or waste) is defined as:
    #    cost = (size of covering network) - (sum of sizes of the individual networks).
    #
    # Precompute a prefix sum of the sizes so that we can quickly compute the total addresses in any segment.
    sizes = [net.num_addresses for net in collapsed]
    prefix_sum = [0] * (m + 1)
    for i in range(m):
        prefix_sum[i+1] = prefix_sum[i] + sizes[i]

    # Precompute the merge cost and the merged network for every possible segment [i, j]
    cost = [[0] * m for _ in range(m)]
    merged_net = [[None] * m for _ in range(m)]
    for i in range(m):
        for j in range(i, m):
            start = collapsed[i].network_address
            end = collapsed[j].broadcast_address
            merged = smallest_covering_network(start, end)
            merged_net[i][j] = merged
            total = prefix_sum[j+1] - prefix_sum[i]  # sum of sizes in collapsed[i..j]
            cost[i][j] = merged.num_addresses - total

    # Now, we want to split the list of m networks into exactly n segments (each segment is contiguous).
    # We use dynamic programming. Let dp[i][s] be the minimum extra addresses ("cost") needed to cover
    # networks from index i to the end using s segments.
    # The recurrence is:
    #    dp[i][1] = cost(i, m-1)
    #    dp[i][s] = min_{j from i to m-s} { cost(i, j) + dp[j+1][s-1] }
    dp = [[float('inf')] * (n+1) for _ in range(m+1)]
    partition = [[-1] * (n+1) for _ in range(m+1)]

    # Base case: if there are no networks left and we need 0 segments, cost is 0.
    dp[m][0] = 0
    # For i < m, dp[i][0] remains infinity (we cannot cover non‐empty list with 0 segments).

    # Fill in the DP table.
    for i in range(m - 1, -1, -1):
        for s in range(1, n+1):
            # We need to leave at least s-1 networks after j, so j goes from i to m - s.
            for j in range(i, m - s + 1):
                current = cost[i][j] + dp[j+1][s-1]
                if current < dp[i][s]:
                    dp[i][s] = current
                    partition[i][s] = j

    # Reconstruct the segmentation using the partition table.
    segments = []
    i, segs_left = 0, n
    while segs_left:
        j = partition[i][segs_left]
        segments.append((i, j))
        i = j + 1
        segs_left -= 1

    # For each segment, get the merged network.
    result = []
    for i, j in segments:
        result.append(str(merged_net[i][j]))

    return result

def read_cidrs_from_file(filepath: str) -> List[str]:
    """
    Read CIDRs from a file, one per line.
    Empty lines and lines starting with # are ignored.
    """
    with open(filepath, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Example usage:
if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print("Error: Please provide an input file path")
        sys.exit(1)

    input_file = sys.argv[1]

    try:
        sample_cidrs = read_cidrs_from_file(input_file)
        # Group into at most 10 CIDRs
        grouped = group_cidrs(sample_cidrs, 10)
        print("Grouped CIDRs:")
        for cidr in grouped:
            print(cidr)
    except FileNotFoundError:
        print(f"Error: Could not find file {input_file}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

