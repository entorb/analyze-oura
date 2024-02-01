# Fetch and analyze your Oura ring data

## Setup

* `pip install -r requirements.txt`
* requires a personal access token, obtained from <https://cloud.ouraring.com/personal-access-tokens> and stored in [token.txt](token.txt)

## Running

* set the start date in [config.json](config.json)
* [1fetch_v2.py](1fetch_v2.py): download your Oura data
* [2analyze_v2.py](2analyze_v2.py): analyze your Oura data

## Results

* correlation of SleepStart and SleepDuration on various parameters
* output as chart and text files
