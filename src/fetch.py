# by Dr. Torben Menke https://entorb.net
# https://github.com/entorb/analyze-oura
"""
Fetch Oura day-summary data from Oura Cloud API.

provide your personal access token in file token.txt
set the start date in config.toml
fetched data is stored in data/
"""

import csv
import json
import tomllib
from pathlib import Path

import requests

Path("data").mkdir(exist_ok=True)

with (Path("src/config.toml")).open("rb") as f:
    config = tomllib.load(f)

try:
    with Path("token.txt").open() as fh:
        token = fh.read().strip()  # trim spaces
except FileNotFoundError:
    msg = "token.txt not found, see README.md for instructions."
    raise FileNotFoundError(msg) from None


def fetch_data_summaries() -> None:
    """
    Fetch data from Oura API.
    """
    for data_summary_set in ("sleep",):  # , "activity", "readiness"
        print(f"fetching {data_summary_set} data")
        url = f"https://api.ouraring.com/v2/usercollection/{data_summary_set}?start_date={config['date_start']}"
        # start=YYYY-MM-DD
        # end=YYYY-MM-DD
        headers = {
            # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:75.0) Gecko/20100101 Firefox/75.0 ", # noqa: E501
            "Authorization": f"Bearer {token}",
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            cont = response.content.decode("utf-8")
        except requests.RequestException as e:
            print(f"Error fetching {data_summary_set} data: {e}")
            continue

        formatted_data_path = Path(f"data/data_{data_summary_set}.json")
        with formatted_data_path.open(mode="w", encoding="utf-8", newline="\n") as fh:
            d = json.loads(cont)
            json.dump(d, fh, ensure_ascii=False, sort_keys=False, indent=True)

            # convert json dict to csv
            # Assume the main data is under the "data" key
            assert "data" in d
            assert isinstance(d["data"], list)
            csv_path = formatted_data_path.with_suffix(".csv")
            with csv_path.open(mode="w", encoding="utf-8", newline="") as fh2:
                writer = csv.DictWriter(fh2, fieldnames=d["data"][0].keys())
                writer.writeheader()
                writer.writerows(d["data"])


if __name__ == "__main__":
    fetch_data_summaries()
