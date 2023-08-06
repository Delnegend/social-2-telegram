#!/usr/bin/env bash
echo "=== Sorting imports ==="
isort --profile black -l 125 .
echo "=== Formatting ==="
black .
echo "=== Linting ==="
ruff . --fix --show-fixes