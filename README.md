# Download and analyze your Oura ring data

## Setup

* requires Python [UV package manager](https://docs.astral.sh/uv/)
* requires a personal access token, obtained from <https://cloud.ouraring.com/personal-access-tokens> and stored as [token.txt](token-EXAMPLE.txt)

## Run

* [config.toml](src/config.toml)
  * set the start date of the data to download
* [fetch.py](src/fetch.py)
  * `uv run src/fetch.py`
  * download your Oura data from Oura API to [data/](data/)
  * alternatively: manually download [sleep.json](https://cloud.ouraring.com/account/export/sleep/json) or [sleep.csv](https://cloud.ouraring.com/account/export/sleep/csv)
* [report.py](src/report.py)
  * `uv run src/report.py`
  * analyze your data
  * generate static reports
  * correlation of SleepStart and SleepDuration on various parameters
  * output as chart (dir [plot/](plot/)) and text file ([sleep_report.txt](report/sleep_report.txt))
* [app.py](src/app.py)
  * `uv run streamlit run src/app.py`
  * interactive visualization using Streamlit

## SonarQube Code Analysis

At [sonarcloud.io](https://sonarcloud.io/summary/overall?id=entorb_analyze-oura&branch=main)
