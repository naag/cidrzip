#!/usr/bin/env python3

import timeit
import random
import ipaddress
from typing import List, Tuple
from cidrzip import CIDRZip
import statistics
import sys

def generate_random_ip() -> str:
    """Generate a random IPv4 address."""
    return f"{random.randint(0, 255)}.{random.randint(0, 255)}." \
           f"{random.randint(0, 255)}.{random.randint(0, 255)}"

def generate_random_prefix() -> int:
    """Generate a random CIDR prefix with weighted distribution."""
    weights = (
        [32] * 20 +  # Individual IPs very common
        [31, 30, 29, 28] * 5 +  # Small subnets common
        [27, 26, 25, 24] * 4 +  # Medium subnets moderately common
        [23, 22, 21, 20] * 2 +  # Larger subnets less common
        [19, 18, 17, 16] * 2 +  # Even larger subnets less common
        [15, 14, 13, 12] +  # Very large subnets rare
        [11, 10, 9, 8]  # Huge subnets very rare
    )
    return random.choice(weights)

def generate_test_data(size: int, distribution: str = "mixed") -> List[str]:
    """Generate test data with different distributions."""
    cidrs = []

    if distribution == "sparse":
        # Generate widely spread individual IPs
        for _ in range(size):
            cidrs.append(f"{generate_random_ip()}/32")

    elif distribution == "dense":
        # Generate IPs within a smaller range
        base_ip = random.randint(0, 255)
        second_octet = random.randint(0, 255)
        for _ in range(size):
            ip = f"{base_ip}.{second_octet}." \
                 f"{random.randint(0, 255)}.{random.randint(0, 255)}"
            cidrs.append(f"{ip}/32")

    elif distribution == "sequential":
        # Generate sequential blocks
        start = random.randint(0, 0xFFFFFFFF - size)
        for i in range(size):
            ip = str(ipaddress.ip_address(start + i))
            cidrs.append(f"{ip}/32")

    else:  # mixed
        while len(cidrs) < size:
            ip = generate_random_ip()
            prefix = generate_random_prefix()
            try:
                network = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
                cidrs.append(str(network))
            except ValueError:
                continue

    return list(set(cidrs))  # Remove any duplicates

def run_benchmark(name: str, cidrs: List[str], n_groups: List[int],
                 repeat: int = 3, number: int = 1) -> List[Tuple[int, float, float, float]]:
    """Run benchmark for given CIDRs and group sizes."""
    zipper = CIDRZip()
    results = []

    print(f"\nRunning benchmark: {name}")
    print(f"Input size: {len(cidrs)} CIDRs")
    print("-" * 60)

    for n in n_groups:
        print(f"Testing with n={n}...", end='', flush=True)

        # Time the operation
        times = timeit.repeat(
            lambda: zipper.group(cidrs, n),
            repeat=repeat,
            number=number
        )

        # Calculate statistics
        avg_time = statistics.mean(times)
        min_time = min(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0

        results.append((n, avg_time, min_time, std_dev))
        print(f" done")
        print(f"  Average time: {avg_time:.3f}s")
        print(f"  Best time:    {min_time:.3f}s")
        print(f"  Std dev:      {std_dev:.3f}s")

    return results

def print_summary(all_results: List[List[str]]):
    """Print a summary of the benchmark results."""
    print("\nBenchmark Summary")
    print("=" * 80)
    print(f"{'Size':>6} {'Distribution':>12} {'Groups':>7} {'Avg(s)':>10} {'Min(s)':>10} {'StdDev':>10}")
    print("-" * 80)

    for result in all_results:
        size, dist, n, avg, min_t, std = result
        print(f"{size:6d} {dist:>12} {n:7d} {float(avg):10.3f} {float(min_t):10.3f} {float(std):10.3f}")

def main():
    # Test configurations - adjusted for real-world scenarios
    sizes = [100, 500, 1000]  # Most common use cases
    distributions = ["sparse", "dense", "sequential", "mixed"]
    n_groups = [1, 10, 25]  # Common target group sizes

    all_results = []

    # Run benchmarks for each configuration
    for size in sizes:
        for dist in distributions:
            name = f"{dist.capitalize()} Distribution ({size} CIDRs)"
            test_data = generate_test_data(size, dist)
            results = run_benchmark(name, test_data, n_groups, repeat=5)  # Increased repeat for better statistics

            for n, avg_time, min_time, std_dev in results:
                all_results.append([
                    size,
                    dist,
                    n,
                    f"{avg_time:.3f}",
                    f"{min_time:.3f}",
                    f"{std_dev:.3f}"
                ])

    # Print summary
    print_summary(all_results)

if __name__ == "__main__":
    # Set random seed for reproducibility
    random.seed(42)
    main()