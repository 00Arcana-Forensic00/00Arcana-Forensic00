# Arcana Forensic Offline Build Makefile

.PHONY: prepare build test verify clean install-deps

PROJECT_DIR := $(shell pwd)
CARGO_CONFIG := $(PROJECT_DIR)/.cargo/config.toml

prepare:
	@echo "Preparing for offline use..."
	@mkdir -p offline_cache/python_packages
	@mkdir -p offline_cache/cargo_vendor
	@mkdir -p offline_cache/test_data
	@pip3 download -r requirements.txt -d ./offline_cache/python_packages --only-binary=:all: || true
	@cargo fetch
	@cargo vendor offline_cache/cargo_vendor > $(CARGO_CONFIG)
	@echo "net.offline = true" >> $(CARGO_CONFIG)
	@echo "Preparation complete. You can now go offline."

build:
	@echo "Building in offline mode..."
	@cargo build --offline --release

test:
	@echo "Running tests offline..."
	@cargo test --offline --release
	@if [ -d demo ]; then cd demo && make test 2>/dev/null || true; fi

verify:
	@echo "Verifying installation..."
	@./target/release/arcana-acquire --version 2>/dev/null || echo "acquire: version check failed"
	@./target/release/arcana-custody --version 2>/dev/null || echo "custody: version check failed"
	@./target/release/arcana-vault --version 2>/dev/null || echo "vault: version check failed"

install-deps:
	@echo "Installing Python dependencies from cache..."
	@pip3 install --no-index --find-links=./offline_cache/python_packages -r requirements.txt

clean:
	@cargo clean
	@rm -rf offline_cache