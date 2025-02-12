.PHONY: test test-verbose test-quiet clean help benchmark profile

PYTHON=python3
TEST_FILE=test_cidrzip.py
BENCHMARK_FILE=benchmark_cidrzip.py
PROFILE_FILE=profile_cidrzip.py

# Default target when no arguments are given
.DEFAULT_GOAL := help

# Run all tests with normal output
test:
	$(PYTHON) -m unittest $(TEST_FILE)

# Run all tests with verbose output
test-verbose:
	$(PYTHON) -m unittest -v $(TEST_FILE)

# Run benchmarks with different optimization modes
benchmark:
	$(PYTHON) $(BENCHMARK_FILE)

# Run profiling with different optimization modes
profile:
	$(PYTHON) $(PROFILE_FILE)

# Remove Python cache files and test artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} +

# Show this help message
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@echo "  test           Run all tests with normal output"
	@echo "  test-verbose   Run all tests with verbose output"
	@echo "  benchmark      Run benchmarks with different optimization modes"
	@echo "  profile        Run profiling with different optimization modes"
	@echo "  clean          Remove Python cache files and test artifacts"
	@echo "  help           Show this help message"