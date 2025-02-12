# cidrzip

A Python tool for efficiently compressing and merging CIDR blocks. It finds the smallest covering network for a range of IP addresses and groups multiple CIDR ranges into a specified number of groups.

## Installation

```bash
git clone https://github.com/naag/cidrzip.git
cd cidrzip
```

## Usage

### Command Line

```bash
# Basic usage - read from file, compress into 5 groups
cidrzip.py -f input.txt -n 5

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

# Group a list of CIDR ranges into 3 groups
cidrs = ["192.168.1.0/24", "10.0.0.0/8", "172.16.0.0/12"]
grouped = zipper.group(cidrs, 3)

# Read CIDRs from a file
cidrs = CIDRZip.read_from_file("path/to/file.txt")
```

## Development

Requirements:
- Python 3.x
- Standard library only (no external dependencies)

## Testing

Run tests using make:
```bash
make test          # Run tests
make test-verbose  # Run tests with verbose output
make clean         # Clean up cache and temporary files
```

## License

MIT License - See LICENSE file for details