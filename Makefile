SHELL := /bin/bash
UV_CACHE_DIR ?= .uv-cache
REF ?= main

RUN := UV_CACHE_DIR=$(UV_CACHE_DIR) uv run

.PHONY: sync test check format tag update-examples build-all weekly-run

sync:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv sync --dev

update-examples:
	$(RUN) python scripts/update_backend_examples.py

test:
	$(RUN) pytest src/narrata/tests
	$(RUN) pytest src/narrata-mcp/tests

check:
	$(RUN) ruff check --config src/narrata/pyproject.toml src/narrata/narrata src/narrata/tests scripts
	$(RUN) ruff format --check --config src/narrata/pyproject.toml src/narrata/narrata src/narrata/tests scripts
	$(RUN) mypy --config-file src/narrata/pyproject.toml src/narrata/narrata
	$(RUN) ruff check --config src/narrata-mcp/pyproject.toml src/narrata-mcp/narrata_mcp src/narrata-mcp/tests
	$(RUN) ruff format --check --config src/narrata-mcp/pyproject.toml src/narrata-mcp/narrata_mcp src/narrata-mcp/tests
	$(RUN) mypy --config-file src/narrata-mcp/pyproject.toml src/narrata-mcp/narrata_mcp

format:
	$(RUN) ruff check --fix --config src/narrata/pyproject.toml src/narrata/narrata src/narrata/tests scripts
	$(RUN) ruff format --config src/narrata/pyproject.toml src/narrata/narrata src/narrata/tests scripts
	$(RUN) ruff check --fix --config src/narrata-mcp/pyproject.toml src/narrata-mcp/narrata_mcp src/narrata-mcp/tests
	$(RUN) ruff format --config src/narrata-mcp/pyproject.toml src/narrata-mcp/narrata_mcp src/narrata-mcp/tests

build-all:
	rm -rf dist src/narrata/dist src/narrata-mcp/dist
	mkdir -p dist
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv build --project src/narrata --out-dir dist
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv build --project src/narrata-mcp --out-dir dist

weekly-run:
	gh workflow run weekly.yml --ref $(REF)

TAG_NAME := $(word 2,$(MAKECMDGOALS))

ifeq (tag,$(firstword $(MAKECMDGOALS)))
  ifeq ($(TAG_NAME),)
    $(error Usage: make tag <version>. Example: make tag 0.1.0)
  endif
  $(eval $(TAG_NAME):;@:)
endif

tag:
	@if [ "$$(git rev-parse --abbrev-ref HEAD)" != "main" ]; then \
		echo "Tagging requires branch 'main'."; \
		exit 1; \
	fi
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "Working tree must be clean before tagging."; \
		exit 1; \
	fi
	@tag="$(TAG_NAME)"; \
	if [[ "$$tag" != v* ]]; then tag="v$$tag"; fi; \
	version="$${tag#v}"; \
	python scripts/bump_release_versions.py "$$version"; \
	git add src/narrata/pyproject.toml src/narrata-mcp/pyproject.toml; \
	if git diff --cached --quiet; then \
		echo "Package versions already at $$version; no commit created."; \
	else \
		git commit -m "chore: release $$version"; \
	fi; \
	if git rev-parse "$$tag" >/dev/null 2>&1; then \
		echo "Tag '$$tag' already exists."; \
		exit 1; \
	fi; \
	git tag -a "$$tag" -m "Release $${tag#v}"
	git push origin main
	@tag="$(TAG_NAME)"; \
	if [[ "$$tag" != v* ]]; then tag="v$$tag"; fi; \
	git push origin "$$tag"
