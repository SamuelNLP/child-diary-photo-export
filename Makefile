-include .env

SHELL = /bin/bash

# =============================================================================
# Development
# =============================================================================

clean_mypy:
	rm -rf .mypy_cache

clean_ruff:
	rm -rf .ruff_cache

clean: clean_mypy clean_ruff

mypy:
	uv run mypy . --ignore-missing-imports --check-untyped-defs

ruff:
	uv run ruff format .
	uv run ruff check . --fix

sync:
	uv sync --all-extras

# =============================================================================
# Building
# =============================================================================

# PyInstaller builds
build-cli:
	uv run build_script.py pyinstaller

build-gui:
	uv run build_script.py pyinstaller-gui

build-pyinstaller: build-cli build-gui

# Briefcase builds
build-briefcase:
	uv run build_script.py briefcase

# Build everything
build: build-pyinstaller

# Clean build artifacts
clean-build:
	uv run python build_script.py clean

# Full clean (dev + build)
full-clean: clean clean-build

# =============================================================================
# Running
# =============================================================================

run: sync
	uv run python -m childdiary_export

run-gui: sync
	uv run python -m childdiary_export --gui

# =============================================================================
# Testing
# =============================================================================

test:
	uv run pytest

# =============================================================================
# Help
# =============================================================================

help:
	@echo "ChildDiary Photo Export - Makefile"
	@echo ""
	@echo "Development:"
	@echo "  make sync              - Install dependencies"
	@echo "  make ruff              - Format and lint code"
	@echo "  make mypy              - Run type checking"
	@echo "  make clean             - Clean dev artifacts"
	@echo ""
	@echo "Building:"
	@echo "  make build-cli         - Build CLI with PyInstaller"
	@echo "  make build-gui         - Build GUI with PyInstaller"
	@echo "  make build-pyinstaller - Build both CLI and GUI with PyInstaller"
	@echo "  make build-briefcase   - Build with Briefcase"
	@echo "  make build             - Build with PyInstaller (CLI + GUI)"
	@echo "  make clean-build       - Clean build artifacts"
	@echo "  make full-clean        - Clean everything"
	@echo ""
	@echo "Running:"
	@echo "  make run               - Run CLI version"
	@echo "  make run-gui           - Run GUI version"
	@echo ""
	@echo "Testing:"
	@echo "  make test              - Run tests"
