#!/bin/sh

# ensure we are in the root dir
cd $(dirname $0)/..

uv run src/fetch.py
uv run src/report.py
uv run streamlit run src/app.py
