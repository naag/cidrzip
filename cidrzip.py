#!/usr/bin/env python3
# Copyright (c) 2025 Peter Bücker
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import ipaddress
from typing import List, Optional, Tuple
import sys
import argparse
import os

class CIDRZip:
    """A class for efficiently compressing and merging CIDR blocks."""

    @staticmethod
    def _cidr_to_ints(cidr: str) -> tuple:
        """Convert a CIDR string directly to integer start and end addresses."""
        network = ipaddress.ip_network(cidr)
        if not isinstance(network, ipaddress.IPv4Network):
            raise TypeError("Only IPv4 networks are supported")
        return (int(network.network_address), int(network.broadcast_address))

    @staticmethod
    def _int_to_network(start_int: int, prefix: int) -> ipaddress.IPv4Network:
        """Convert an integer and prefix to an IPv4Network."""
        if not 0 <= prefix <= 32:
            raise ValueError("IPv4 prefix must be between 0 and 32")
        start_addr = str(ipaddress.IPv4Address(start_int))
        return ipaddress.ip_network(f"{start_addr}/{prefix}", strict=False)

    @staticmethod
    def smallest_covering_network_ints(start_int: int, end_int: int) -> tuple:
        """
        Given start and end as integers, returns the smallest network that covers the range.
        Returns (start_int, prefix_len).
        """
        diff = start_int ^ end_int
        prefix = 32 if diff == 0 else 32 - diff.bit_length()
        # Mask the start address to ensure it's the network address
        mask = ((1 << 32) - 1) << (32 - prefix)
        network_int = start_int & mask
        return (network_int, prefix)

    def _merge_networks_greedy(self, collapsed: list, n: int) -> List[str]:
        """
        Greedy approach to merge networks. Merges adjacent networks with lowest cost first.
        """
        while len(collapsed) > n:
            # Find the best merge (lowest cost)
            best_cost = float('inf')
            best_idx = -1

            for i in range(len(collapsed) - 1):
                start = collapsed[i][0]
                end = collapsed[i + 1][1]
                net_int, prefix = self.smallest_covering_network_ints(start, end)
                size = 1 << (32 - prefix)
                current_size = collapsed[i][1] - collapsed[i][0] + 1
                current_size += collapsed[i + 1][1] - collapsed[i + 1][0] + 1
                cost = size - current_size

                if cost < best_cost:
                    best_cost = cost
                    best_idx = i

            # Merge the best pair
            start = collapsed[best_idx][0]
            end = collapsed[best_idx + 1][1]
            collapsed[best_idx] = (start, end)
            collapsed.pop(best_idx + 1)

        # Convert to CIDR strings
        result = []
        for start, end in collapsed:
            net_int, prefix = self.smallest_covering_network_ints(start, end)
            result.append(str(self._int_to_network(net_int, prefix)))
        return result

    def _merge_networks_windowed(self, collapsed: list, n: int, window_size: int) -> List[str]:
        """
        Dynamic programming approach that only considers merging within a fixed window size.
        """
        m = len(collapsed)
        if window_size > m:
            window_size = m

        # Precompute sizes for quick segment size computation
        sizes = [(end - start + 1) for start, end in collapsed]
        prefix_sum = [0] * (m + 1)
        for i in range(m):
            prefix_sum[i+1] = prefix_sum[i] + sizes[i]

        # Precompute merge costs and merged networks for all possible segments within window
        cost = [[float('inf')] * m for _ in range(m)]
        merged_net = [[None] * m for _ in range(m)]
        for i in range(m):
            for j in range(i, min(i + window_size, m)):
                start = collapsed[i][0]
                end = collapsed[j][1]
                net_int, prefix = self.smallest_covering_network_ints(start, end)
                size = 1 << (32 - prefix)
                merged_net[i][j] = (net_int, prefix)
                total = prefix_sum[j+1] - prefix_sum[i]
                cost[i][j] = size - total

        # Dynamic programming with window constraint
        dp = [[float('inf')] * (n+1) for _ in range(m+1)]
        partition = [[-1] * (n+1) for _ in range(m+1)]

        dp[m][0] = 0  # Base case: no networks left, 0 segments needed

        for i in range(m - 1, -1, -1):
            for s in range(1, n+1):
                for j in range(i, min(i + window_size, m - s + 1)):
                    current = cost[i][j] + dp[j+1][s-1]
                    if current < dp[i][s]:
                        dp[i][s] = current
                        partition[i][s] = j

        # Reconstruct the optimal segmentation
        segments = []
        i, segs_left = 0, n
        while segs_left:
            j = partition[i][segs_left]
            if j == -1:  # No valid solution found
                # Fall back to greedy for remaining segments
                remaining = [(start, end) for start, end in collapsed[i:]]
                greedy_result = self._merge_networks_greedy(remaining, segs_left)
                segments.extend([(i+idx, i+idx) for idx in range(len(greedy_result))])
                break
            segments.append((i, j))
            i = j + 1
            segs_left -= 1

        # Convert segments to CIDR strings
        result = []
        for i, j in segments:
            if i == j:  # Single network
                start, end = collapsed[i]
                net_int, prefix = self.smallest_covering_network_ints(start, end)
                result.append(str(self._int_to_network(net_int, prefix)))
            else:  # Merged network
                net_int, prefix = merged_net[i][j]
                result.append(str(self._int_to_network(net_int, prefix)))
        return result

    def group(self, cidrs: List[str], n: int, mode: str = 'optimal', window_size: int = 50) -> List[str]:
        """
        Group a list of CIDR strings into at most n larger, non-overlapping CIDR ranges.

        Args:
            cidrs: List of CIDR strings to group
            n: Maximum number of groups to create
            mode: One of 'optimal' (default), 'greedy', or 'windowed'
            window_size: For windowed mode, max distance to consider merging (default: 50)
        """
        if not cidrs:
            return []

        # Convert CIDRs to integer ranges and sort by start address
        ranges = [self._cidr_to_ints(c) for c in cidrs]
        ranges.sort()  # Sort by start address

        # Collapse overlapping ranges
        collapsed = []
        current_start, current_end = ranges[0]

        for start, end in ranges[1:]:
            if start <= current_end + 1:
                current_end = max(current_end, end)
            else:
                collapsed.append((current_start, current_end))
                current_start, current_end = start, end
        collapsed.append((current_start, current_end))

        m = len(collapsed)

        # If we already have n or fewer groups, convert back to CIDRs and return
        if n >= m:
            result = []
            for start, end in collapsed:
                net_int, prefix = self.smallest_covering_network_ints(start, end)
                result.append(str(self._int_to_network(net_int, prefix)))
            return result

        # Choose merging strategy based on mode
        if mode == 'greedy':
            return self._merge_networks_greedy(collapsed, n)
        elif mode == 'windowed':
            return self._merge_networks_windowed(collapsed, n, window_size)
        else:  # optimal mode
            return self._merge_networks_windowed(collapsed, n, m)  # window_size=m means consider all pairs

    @staticmethod
    def read_from_file(filepath: str) -> List[str]:
        """
        Read CIDRs from a file, one per line or space-separated.
        Empty lines and lines starting with # are ignored.

        Args:
            filepath: Path to the file containing CIDR ranges, use - for stdin

        Returns:
            List of CIDR strings from the file
        """
        with open(filepath, 'r') if filepath != '-' else sys.stdin as f:
            cidrs = []
            for line in f:
                if line.strip() and not line.startswith('#'):
                    # Split on whitespace and add non-empty CIDRs
                    cidrs.extend(cidr for cidr in line.strip().split() if cidr)
            return cidrs

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

def main():
    """Main entry point for the cidrzip command-line tool."""
    parser = argparse.ArgumentParser(
        description='Efficiently compress and merge CIDR blocks into a specified number of groups.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s -f input.txt -n 5          # Compress CIDRs from file into 5 groups (optimal mode)
  %(prog)s -f input.txt -n 5 --greedy # Use faster greedy mode
  %(prog)s -f input.txt -n 5 -w 10    # Use windowed mode with window size 10
  %(prog)s -f input.txt --json        # Output in JSON format
  %(prog)s -f input.txt --one-per-line  # Output one CIDR per line
  %(prog)s -f - -n 3                  # Read from stdin, compress to 3 groups
        '''
    )

    parser.add_argument('-f', '--file',
                       type=str,
                       required=True,
                       help='Input file containing CIDR ranges (one per line), use - for stdin')

    parser.add_argument('-n', '--num-groups',
                       type=int,
                       default=10,
                       help='Maximum number of groups to create (default: 10)')

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--greedy',
                           action='store_true',
                           help='Use greedy mode (faster but may be less optimal)')
    mode_group.add_argument('-w', '--window',
                           type=int,
                           metavar='SIZE',
                           help='Use windowed mode with specified window size')

    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument('--json',
                            action='store_true',
                            help='Output results in JSON format')
    format_group.add_argument('--one-per-line',
                            action='store_true',
                            help='Output one CIDR per line (default)')

    parser.add_argument('-q', '--quiet',
                       action='store_true',
                       help='Suppress informational output')

    args = parser.parse_args()

    try:
        # Handle stdin if file is '-'
        if args.file == '-':
            if not sys.stdin.isatty():
                zipper = CIDRZip()
                cidrs = zipper.read_from_file('-')  # Use the class's built-in handling
            else:
                parser.error("No input provided on stdin")
        else:
            zipper = CIDRZip()
            cidrs = zipper.read_from_file(args.file)

        if not cidrs:
            if not args.quiet:
                print("Warning: No valid CIDR ranges found in input", file=sys.stderr)
            sys.exit(0)

        # Determine mode and parameters
        if args.greedy:
            mode = 'greedy'
            window_size = None
        elif args.window is not None:
            mode = 'windowed'
            window_size = args.window
        else:
            mode = 'optimal'
            window_size = None

        # Group the CIDRs
        zipper = CIDRZip()
        if mode == 'windowed':
            result = zipper.group(cidrs, args.num_groups, mode=mode, window_size=window_size)
        else:
            result = zipper.group(cidrs, args.num_groups, mode=mode)

        # Output the results without extra newlines
        if args.json:
            import json
            print(json.dumps(result), end='')
        else:  # one per line (default)
            print('\n'.join(result), end='')

        if not args.quiet:
            print(f"\nCompressed {len(cidrs)} CIDR(s) into {len(result)} group(s) using {mode} mode",
                  file=sys.stderr)

    except FileNotFoundError:
        parser.error(f"Could not find file: {args.file}")
    except ValueError as e:
        parser.error(str(e))
    except KeyboardInterrupt:
        sys.exit(130)  # Standard Unix practice: 128 + SIGINT's signal number (2)
    except BrokenPipeError:
        # Python flushes standard streams on exit; redirect remaining output
        # to devnull to avoid another BrokenPipeError at shutdown
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)

if __name__ == '__main__':
    main()

