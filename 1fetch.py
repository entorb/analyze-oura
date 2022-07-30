#!/usr/bin/env python3
# by Dr. Torben Menke https://entorb.net
# https://github.com/entorb/analyze-oura

"""
fetches Oura day-summary data from Oura Cloud API
requires a personal access token from https://cloud.ouraring.com/personal-access-tokens
provide your personal access token in file token.txt
set the start date in config.json
fetched data is stored in data/
"""

import json
import os

import requests

os.makedirs("data", exist_ok=True)

with open("config.json", mode="r", encoding="utf-8") as fh:
    config = json.load(fh)

with open("token.txt", mode="r") as fh:
    token = fh.read()
    token = token.strip()  # trim spaces


def fetch_data_summaries():
    for data_summary_set in ("sleep", "activity", "readiness"):
        print(f"fetching {data_summary_set} data")
        # url = "https://api.ouraring.com/v1/sleep"
        # -> last week
        url = f"https://api.ouraring.com/v1/{data_summary_set}?start={config['date_start']}"
        # start=YYYY-MM-DD
        # end=YYYY-MM-DD
        headers = {
            #    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:75.0) Gecko/20100101 Firefox/75.0 ",
            "Authorization": f"Bearer {token}"
        }
        cont = requests.get(url, headers=headers).content
        cont = cont.decode("utf-8")

        with open(
            f"data/data_raw_{data_summary_set}.json",
            mode="w",
            encoding="utf-8",
            newline="\n",
        ) as fh:
            fh.write(cont)
        with open(
            f"data/data_formatted_{data_summary_set}.json",
            mode="w",
            encoding="utf-8",
            newline="\n",
        ) as fh:
            d = json.loads(cont)
            json.dump(d, fh, ensure_ascii=False, sort_keys=False, indent=True)


if __name__ == "__main__":
    fetch_data_summaries()
