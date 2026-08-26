#!/bin/sh

# ensure we are in the root dir
cd $(dirname $0)/..

# exit upon error
set -e

# remove all dependencies
uv remove matplotlib numpy pandas requests streamlit
uv remove --dev ruff watchdog

uv lock --upgrade
uv sync --upgrade

# to update uv on macos:
# brew update && brew upgrade uv

uv python upgrade

# re-add all dependencies
uv add matplotlib numpy pandas requests streamlit
uv add --dev ruff watchdog

uv lock --upgrade
uv sync --upgrade

# ruff
uv run ruff format
uv run ruff check --fix

# pre-commit
prek autoupdate
prek run --all-files

echo DONE
