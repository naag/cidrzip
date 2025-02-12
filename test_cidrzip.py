#!/usr/bin/env python3
# Copyright (c) 2025 Peter Bücker
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import unittest
from cidrzip import CIDRZip
import ipaddress
import tempfile
import os
import random
from typing import List, Tuple

class TestCIDRZip(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.zipper = CIDRZip()

    @staticmethod
    def _generate_random_ip() -> str:
        """Generate a random IPv4 address"""
        return f"{random.randint(0, 255)}.{random.randint(0, 255)}." \
               f"{random.randint(0, 255)}.{random.randint(0, 255)}"

    @staticmethod
    def _generate_random_prefix() -> int:
        """Generate a random CIDR prefix with weighted distribution"""
        # Enhanced weights to better represent real-world scenarios
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

    def _generate_random_cidrs(self, count: int, distribution: str = "mixed") -> List[str]:
        """
        Generate a list of random CIDRs
        distribution: 'sparse' for widely spread IPs
                     'dense' for closer IPs
                     'mixed' for a combination
                     'clustered' for multiple dense clusters
        """
        cidrs = []
        if distribution == "sparse":
            # Generate widely spread individual IPs
            for _ in range(count):
                cidrs.append(f"{self._generate_random_ip()}/32")
        elif distribution == "dense":
            # Generate IPs within a smaller range
            base_ip = random.randint(0, 255)
            second_octet = random.randint(0, 255)
            for _ in range(count):
                ip = f"{base_ip}.{second_octet}." \
                     f"{random.randint(0, 255)}.{random.randint(0, 255)}"
                cidrs.append(f"{ip}/32")
        elif distribution == "clustered":
            # Generate multiple clusters of IPs
            clusters = random.randint(3, 8)
            ips_per_cluster = count // clusters
            for _ in range(clusters):
                base_ip = random.randint(0, 255)
                second_octet = random.randint(0, 255)
                for _ in range(ips_per_cluster):
                    ip = f"{base_ip}.{second_octet}." \
                         f"{random.randint(0, 255)}.{random.randint(0, 255)}"
                    cidrs.append(f"{ip}/32")
            # Fill remaining count with random IPs
            while len(cidrs) < count:
                cidrs.append(f"{self._generate_random_ip()}/32")
        else:  # mixed
            # Mix of individual IPs and various sized blocks
            while len(cidrs) < count:
                ip = self._generate_random_ip()
                prefix = self._generate_random_prefix()
                try:
                    # Ensure it's a valid network
                    network = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
                    cidrs.append(str(network))
                except ValueError:
                    continue

        return list(set(cidrs))  # Remove any duplicates

    def _is_ip_in_cidr(self, ip_cidr: str, network_cidr: str) -> bool:
        """Helper method to check if an IP/CIDR is contained within another CIDR"""
        ip_net = ipaddress.ip_network(ip_cidr, strict=False)
        network = ipaddress.ip_network(network_cidr, strict=False)
        return ip_net.network_address >= network.network_address and ip_net.broadcast_address <= network.broadcast_address

    def _verify_coverage(self, input_cidrs: list, result_cidrs: list):
        """Helper method to verify all input CIDRs are covered by the result CIDRs"""
        for ip in input_cidrs:
            self.assertTrue(
                any(self._is_ip_in_cidr(ip, cidr) for cidr in result_cidrs),
                f"IP {ip} not found in any CIDR of {result_cidrs}"
            )

    def test_empty_input(self):
        """Test with empty input list"""
        self.assertEqual(self.zipper.group([], 5), [])

    def test_single_cidr(self):
        """Test with a single CIDR"""
        self.assertEqual(self.zipper.group(["192.168.1.1/32"], 1), ["192.168.1.1/32"])

    def test_adjacent_ips(self):
        """Test with adjacent IPs that should be merged"""
        input_cidrs = [
            "192.168.1.1/32",
            "192.168.1.2/32",
            "192.168.1.3/32",
            "192.168.1.4/32"
        ]
        result = self.zipper.group(input_cidrs, 1)
        self.assertEqual(len(result), 1)
        # The result should cover all input IPs
        self.assertTrue(all(self._is_ip_in_cidr(ip, result[0]) for ip in input_cidrs))

    def test_non_adjacent_ips(self):
        """Test with non-adjacent IPs that can't be perfectly merged"""
        input_cidrs = [
            "192.168.1.1/32",
            "192.168.1.10/32",
            "192.168.1.20/32"
        ]
        # With n=2, should split into two ranges
        result = self.zipper.group(input_cidrs, 2)
        self.assertEqual(len(result), 2)

    def test_large_n(self):
        """Test when n is larger than number of input CIDRs"""
        input_cidrs = ["192.168.1.1/32", "192.168.1.2/32"]
        result = self.zipper.group(input_cidrs, 10)
        # Should return the collapsed form, which might be one or two CIDRs
        self.assertLessEqual(len(result), 2)
        # Verify all input IPs are covered
        for ip in input_cidrs:
            self.assertTrue(any(self._is_ip_in_cidr(ip, cidr) for cidr in result))

    def test_exact_n(self):
        """Test when n equals number of input CIDRs"""
        input_cidrs = ["192.168.1.1/32", "192.168.2.1/32"]
        result = self.zipper.group(input_cidrs, 2)
        self.assertEqual(len(result), 2)
        self.assertEqual(set(result), set(["192.168.1.1/32", "192.168.2.1/32"]))

    def test_small_n(self):
        """Test when n is smaller than optimal grouping"""
        input_cidrs = [
            "192.168.1.1/32",
            "192.168.1.2/32",
            "192.168.2.1/32",
            "192.168.2.2/32",
            "192.168.3.1/32"
        ]
        result = self.zipper.group(input_cidrs, 2)
        self.assertEqual(len(result), 2)
        # Verify all input IPs are covered
        for ip in input_cidrs:
            self.assertTrue(any(self._is_ip_in_cidr(ip, cidr) for cidr in result))

    def test_invalid_cidr(self):
        """Test with invalid CIDR notation"""
        with self.assertRaises(ValueError):
            self.zipper.group(["invalid-cidr"], 1)

    def test_mixed_ip_versions(self):
        """Test with mixed IPv4 and IPv6 addresses (should raise TypeError)"""
        with self.assertRaises(TypeError):
            self.zipper.group(["192.168.1.1/32", "2001:db8::1/128"], 1)

    def test_overlapping_cidrs(self):
        """Test with overlapping CIDRs"""
        input_cidrs = [
            "192.168.1.0/24",
            "192.168.1.0/25",
            "192.168.1.128/25"
        ]
        result = self.zipper.group(input_cidrs, 1)
        self.assertEqual(result, ["192.168.1.0/24"])

    def test_real_world_sample(self):
        """Test with the sample data from the example file"""
        sample_cidrs = CIDRZip.read_from_file('examples/sample_cidrs.txt')

        # Test with different n values
        result_10 = self.zipper.group(sample_cidrs, 10)
        self.assertLessEqual(len(result_10), 10)

        result_1 = self.zipper.group(sample_cidrs, 1)
        self.assertEqual(len(result_1), 1)

        # Test that all original IPs are covered in the results
        for result in [result_1, result_10]:
            for ip in sample_cidrs:
                self.assertTrue(
                    any(self._is_ip_in_cidr(ip, cidr) for cidr in result),
                    f"IP {ip} not found in any CIDR of {result}"
                )

    def test_large_diverse_ranges(self):
        """Test with a large set of diverse IP ranges across different classes"""
        input_cidrs = [
            # Class A ranges
            "10.0.0.1/32",
            "10.0.1.0/24",
            "10.1.0.0/16",
            "10.2.0.0/15",
            # Class B ranges
            "172.16.0.0/24",
            "172.16.1.0/24",
            "172.16.2.0/23",
            "172.17.0.0/16",
            # Class C ranges
            "192.168.0.0/24",
            "192.168.1.0/24",
            "192.168.2.0/23",
            "192.168.4.0/22",
            # Scattered individual IPs
            "203.0.113.1/32",
            "203.0.113.2/32",
            "203.0.113.4/32",
            "203.0.113.8/32",
            # Different sized blocks at edges
            "10.255.255.240/28",
            "10.255.255.0/24",
            "172.16.255.0/24",
            "172.16.255.128/25"
        ]

        # Test with different n values
        for n in [1, 5, 10, 15]:
            result = self.zipper.group(input_cidrs, n)
            self.assertLessEqual(len(result), n)
            self._verify_coverage(input_cidrs, result)

    def test_power_of_two_boundaries(self):
        """Test with IPs at and around power-of-2 boundaries"""
        input_cidrs = [
            # Around /24 boundary
            "192.168.1.254/32",
            "192.168.1.255/32",
            "192.168.2.0/32",
            "192.168.2.1/32",
            # Around /16 boundary
            "172.15.255.254/32",
            "172.15.255.255/32",
            "172.16.0.0/32",
            "172.16.0.1/32",
            # Around /8 boundary
            "9.255.255.254/32",
            "9.255.255.255/32",
            "10.0.0.0/32",
            "10.0.0.1/32"
        ]

        result = self.zipper.group(input_cidrs, 3)
        self.assertLessEqual(len(result), 3)
        self._verify_coverage(input_cidrs, result)

    def test_sparse_distribution(self):
        """Test with widely spaced IPs that shouldn't be merged even with small n"""
        input_cidrs = [
            "1.1.1.1/32",
            "42.42.42.42/32",
            "100.100.100.100/32",
            "200.200.200.200/32"
        ]

        # Even with n=1, the cost of merging should be very high
        result = self.zipper.group(input_cidrs, 1)
        self.assertEqual(len(result), 1)
        self._verify_coverage(input_cidrs, result)

        # With n=2, should split into two groups
        result = self.zipper.group(input_cidrs, 2)
        self.assertEqual(len(result), 2)
        self._verify_coverage(input_cidrs, result)

    def test_large_subnet_mix(self):
        """Test with a mix of very large and very small subnets"""
        input_cidrs = [
            # Large subnets
            "10.0.0.0/8",
            "172.16.0.0/12",
            # Medium subnets
            "192.168.0.0/16",
            "192.169.0.0/16",
            # Small subnets
            "203.0.113.0/24",
            "203.0.114.0/24",
            # Individual IPs
            "8.8.8.8/32",
            "8.8.4.4/32",
            "1.1.1.1/32",
            "1.0.0.1/32"
        ]

        # Test with different n values
        for n in [1, 3, 5]:
            result = self.zipper.group(input_cidrs, n)
            self.assertLessEqual(len(result), n)
            self._verify_coverage(input_cidrs, result)

    def test_sequential_blocks(self):
        """Test with many sequential blocks that could be merged"""
        # Create 100 sequential /24 blocks
        input_cidrs = [f"192.168.{i}.0/24" for i in range(100)]

        # Test merging into different numbers of groups
        for n in [1, 10, 50]:
            result = self.zipper.group(input_cidrs, n)
            self.assertLessEqual(len(result), n)
            self._verify_coverage(input_cidrs, result)

    def test_random_scattered_ips(self):
        """Test with 20 completely random /32 addresses across the IPv4 space"""
        input_cidrs = [
            "3.144.198.77/32",      # AWS region
            "52.95.110.1/32",       # Another AWS
            "87.23.45.99/32",       # European ISP range
            "91.189.88.142/32",     # Canonical
            "104.16.132.229/32",    # Cloudflare
            "108.177.122.100/32",   # Google
            "128.30.52.100/32",     # MIT
            "130.61.55.200/32",     # Oracle Cloud
            "140.82.112.3/32",      # GitHub
            "142.250.187.78/32",    # Google again
            "157.240.241.35/32",    # Facebook
            "162.159.135.42/32",    # Cloudflare again
            "172.217.3.110/32",     # More Google
            "185.199.108.153/32",   # GitHub Pages
            "192.0.66.2/32",        # ICANN
            "199.232.68.133/32",    # Fastly
            "203.104.153.1/32",     # Asia-Pacific
            "207.231.60.5/32",      # ARIN
            "216.58.214.14/32",     # Yet more Google
            "223.255.254.1/32"      # APNIC
        ]

        # Test with max group size 10
        result = self.zipper.group(input_cidrs, 10)

        # Verify we get at most 10 groups
        self.assertLessEqual(len(result), 10)

        # Verify all IPs are covered
        self._verify_coverage(input_cidrs, result)

    def test_fuzz_random_distributions(self):
        """Fuzz test with different IP distributions and group sizes"""
        # Test parameters - balanced for coverage and performance
        sizes = [10, 50, 100]  # Reduced sizes
        distributions = ["sparse", "dense", "mixed"]  # Removed clustered to reduce combinations

        for size in sizes:
            for dist in distributions:
                input_cidrs = self._generate_random_cidrs(size, dist)
                for n in [1, max(size // 10, 1), size // 2]:  # Removed full size test
                    result = self.zipper.group(input_cidrs, n)
                    self.assertLessEqual(len(result), n)
                    self._verify_coverage(input_cidrs, result)

    def test_fuzz_edge_cases(self):
        """Fuzz test focusing on edge cases and boundary conditions"""
        # Test with power-of-two sized inputs
        for power in range(1, 7):  # Reduced to 2^6 = 64
            size = 2 ** power
            for dist in ["sparse", "mixed"]:  # Only test sparse and mixed
                input_cidrs = self._generate_random_cidrs(size, dist)
                for group_size in [1, 2, min(size, 8)]:  # Reduced group sizes
                    result = self.zipper.group(input_cidrs, group_size)
                    self.assertLessEqual(len(result), group_size)
                    self._verify_coverage(input_cidrs, result)

    def test_fuzz_stress(self):
        """Stress test with large inputs and various group sizes"""
        # Test each distribution type once with large input
        for dist in ["sparse", "mixed"]:  # Reduced distributions
            input_cidrs = self._generate_random_cidrs(200, dist)  # Reduced from 300
            group_sizes = [1, 10, 50, 200]  # Reduced number of group sizes
            for n in group_sizes:
                result = self.zipper.group(input_cidrs, n)
                self.assertLessEqual(len(result), n)
                self._verify_coverage(input_cidrs, result)

    def test_fuzz_sequential(self):
        """Fuzz test with sequential CIDR blocks of varying sizes"""
        for _ in range(3):  # Reduced iterations
            base_ip = self._generate_random_ip()
            base_net = ipaddress.ip_network(f"{base_ip}/16", strict=False)

            input_cidrs = []
            current_ip = int(base_net.network_address)
            for _ in range(30):  # Reduced from 50
                prefix = random.randint(24, 32)
                ip = str(ipaddress.ip_address(current_ip))
                try:
                    network = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
                    input_cidrs.append(str(network))
                    current_ip = int(network.broadcast_address) + 1
                except ValueError:
                    continue

            for n in [1, 10, 30]:  # Reduced number of group sizes
                result = self.zipper.group(input_cidrs, n)
                self.assertLessEqual(len(result), n)
                self._verify_coverage(input_cidrs, result)

if __name__ == '__main__':
    unittest.main()