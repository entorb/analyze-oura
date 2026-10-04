#!/bin/sh
set -e
cd "$(dirname "$0")/.."

uv run src/fetch.py
uv run src/report.py
uv run streamlit run src/app.py
