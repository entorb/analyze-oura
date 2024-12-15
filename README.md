# Fetch and analyze your Oura ring data

## Setup

* `pip install -r requirements.txt`
* requires a personal access token, obtained from <https://cloud.ouraring.com/personal-access-tokens> and stored as [token.txt](token.txt)

## Run

* set the start date in [config.toml](src/config.toml)
* [fetch.py](src/fetch.py): download your Oura data to [data/](data/)
* [report.py](src/report.py): analyze your Oura data
* [app.py](src/app.py): Streamlit visualization

## Results

* correlation of SleepStart and SleepDuration on various parameters
* output as chart (dir [plot/](plot/)) and text file ([sleep_report.txt](report/sleep_report.txt))
