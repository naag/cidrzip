# cidrzip

A Python tool for efficiently compressing and merging CIDR blocks. It finds the smallest covering network for a range of IP addresses and groups multiple CIDR ranges into a specified number of groups.

## Quick Usage

```bash
# Compress multiple CIDRs into 3 groups
echo "192.168.1.0/24 10.0.0.0/8 172.16.0.0/12 192.168.2.0/24 10.10.0.0/16" | ./cidrzip.py -f -

# Output:
# 10.0.0.0/8
# 172.16.0.0/12
# 192.168.0.0/23
```

## Installation

```bash
git clone https://github.com/naag/cidrzip.git
cd cidrzip
```

## Usage

### Command Line

```bash
# Basic usage - read from file, compress into 5 groups (optimal mode)
cidrzip.py -f input.txt -n 5

# Use faster greedy mode
cidrzip.py -f input.txt -n 5 --greedy

# Use windowed mode with custom window size
cidrzip.py -f input.txt -n 5 -w 10

# Read from stdin
cat input.txt | cidrzip.py -f - -n 3

# Output in JSON format
cidrzip.py -f input.txt --json

# Suppress informational messages
cidrzip.py -f input.txt -q
```

For all options:
```bash
cidrzip.py --help
```

### Python API

```python
from cidrzip import CIDRZip

# Create a zipper instance
zipper = CIDRZip()

# Group using optimal mode (default)
cidrs = ["192.168.1.0/24", "10.0.0.0/8", "172.16.0.0/12"]
grouped = zipper.group(cidrs, 3)

# Use faster greedy mode
grouped = zipper.group(cidrs, 3, mode='greedy')

# Use windowed mode with custom window size
grouped = zipper.group(cidrs, 3, mode='windowed', window_size=10)

# Read CIDRs from a file
cidrs = CIDRZip.read_from_file("path/to/file.txt")
```

### Optimization Modes

The tool supports three optimization modes for different performance/quality tradeoffs:

1. **Optimal Mode** (default)
   - Finds the mathematically optimal grouping
   - Slowest but gives best results
   - Best for small to medium inputs or when quality is critical

2. **Greedy Mode** (`--greedy` or `mode='greedy'`)
   - Uses a fast greedy algorithm
   - Much faster (20-30x) but may give suboptimal results
   - Good for large inputs or when speed is critical

3. **Windowed Mode** (`-w SIZE` or `mode='windowed'`)
   - Compromise between optimal and greedy
   - Only considers merging networks within a fixed window
   - Window size controls speed/quality tradeoff:
     - Smaller window = faster but less optimal
     - Larger window = slower but more optimal
   - Good default choice for large inputs

Performance comparison (8000+ CIDRs, n=500):
- Optimal: ~7s
- Windowed (size=50): ~1.2s
- Windowed (size=10): ~0.45s
- Greedy: ~0.23s

*Benchmark environment: MacBook Air M1 (8GB), Python 3.13.2. Your results may vary depending on hardware and input characteristics.*

## Development

Requirements:
- Python 3.x
- Standard library only (no external dependencies)

## Testing and Performance

Run tests and benchmarks using make:
```bash
make test          # Run tests
make test-verbose  # Run tests with verbose output
make benchmark     # Run benchmarks with different optimization modes
make profile       # Run detailed profiling analysis
make clean         # Clean up cache and temporary files
```

Performance comparison (8000+ CIDRs, n=500):
- Optimal: ~7s
- Windowed (size=50): ~1.2s
- Windowed (size=10): ~0.45s
- Greedy: ~0.23s

*Benchmark environment: MacBook Air M1 (8GB), Python 3.13.2. Your results may vary depending on hardware and input characteristics.*

You can run your own benchmarks and profiling to compare performance on your system using the make commands above.

## License

MIT License - See LICENSE file for details