-include .env

SHELL = /bin/bash

clean_mypy:
	rm -rf .mypy_cache

clean_ruff:
	rm -rf .ruff_cache

clean: clean_mypy clean_ruff

mypy:
	poetry run mypy . --ignore-missing-imports --check-untyped-defs

ruff:
	poetry run ruff format .
	poetry run ruff check . --fix