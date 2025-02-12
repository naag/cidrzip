.PHONY: test test-verbose test-quiet clean help

PYTHON=python3
TEST_FILE=test_cidrzip.py

# Default target when no arguments are given
.DEFAULT_GOAL := help

# Run all tests with normal output
test:
	$(PYTHON) -m unittest $(TEST_FILE)

# Run all tests with verbose output
test-verbose:
	$(PYTHON) -m unittest -v $(TEST_FILE)

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
	@echo ""
	@awk '/^[a-zA-Z_-]+:/ { \
		if (match(lastline, /^# /)) { \
			printf "  %-15s %s\n", substr($$1, 1, length($$1)-1), substr(lastline, 3); \
		} \
	} \
	{ lastline = $$0 }' $(MAKEFILE_LIST)