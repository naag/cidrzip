# cidrzip

A Python tool for efficiently compressing and merging CIDR blocks. It finds the smallest covering network for a range of IP addresses and groups multiple CIDR ranges into a specified number of groups.

## Installation

```bash
git clone https://github.com/naag/cidrzip.git
cd cidrzip
```

## Usage

```python
from cidr_grouping import group_cidrs

# Group a list of CIDR ranges into 3 groups
cidrs = ["192.168.1.0/24", "10.0.0.0/8", "172.16.0.0/12"]
grouped = group_cidrs(cidrs, 3)
```

You can also read CIDR ranges from a file:
```python
from cidr_grouping import read_cidrs_from_file

cidrs = read_cidrs_from_file("path/to/file.txt")
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