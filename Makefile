.PHONY: help requirements upgrade lint format test clean

.DEFAULT_GOAL := help

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

requirements:  ## Sync dev dependencies
	uv sync --group dev
	uv tool install tox --with tox-uv

upgrade:  ## Upgrade and regenerate pinned dependencies
	uv run --with edx-lint edx_lint write_uv_constraints pyproject.toml
	uv lock --upgrade

lint:  ## Run linting checks
	uv run tox -e lint

format:  ## Auto-fix formatting and import order issues
	uv run ruff check --fix .
	uv run ruff format .

test:  ## Run tests
	uv run tox -e py311-test

clean:  ## Clean cache, test, and build directories
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .ruff_cache/ htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
