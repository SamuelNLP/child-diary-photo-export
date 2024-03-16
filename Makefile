-include .env

SHELL = /bin/bash
PACKAGE_VERSION:=$(shell git describe --tags --abbrev=0)
DOCKER_REGISTRY=europe-docker.pkg.dev/$(PROJECT_ID)/$(ARTIFACT_REGISTRY)
IMAGE_NAME=ai-<name-placeholder>-server

clean_dist:
	rm -rf dist *.egg-info

clean_tests:
	rm -rf .pytest_cache .tox .coverage htmlcov test_report.xml
	py3clean .

clean_mypy:
	rm -rf .mypy_cache

clean_ruff:
	rm -rf .ruff_cache

clean: clean_dist clean_mypy clean_tests clean_ruff

test:
	poetry run pytest -v -p no:cacheprovider tests

test_w_coverage:
	poetry run pytest -v --junitxml=unit_test_report.xml --cov-report html --cov=<name-placeholder-underscore> tests/

package: clean_dist
	poetry build

mypy:
	poetry run mypy . --ignore-missing-imports --check-untyped-defs

ruff:
	poetry run ruff format .
	poetry run ruff check . --fix