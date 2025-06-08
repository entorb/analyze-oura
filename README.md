# Download and analyze your Oura ring data

## Setup

* `pip install -r requirements.txt`
* requires a personal access token, obtained from <https://cloud.ouraring.com/personal-access-tokens> and stored as [token.txt](token-EXAMPLE.txt)

## Run

* [config.toml](src/config.toml)
  * set the start date of the data to download
* [fetch.py](src/fetch.py)
  * download your Oura data to [data/](data/)
  * alternatively: manually download [sleep.json](https://cloud.ouraring.com/account/export/sleep/json) or [sleep.csv](https://cloud.ouraring.com/account/export/sleep/csv)
* [report.py](src/report.py)
  * analyze your data
  * generate static reports
  * correlation of SleepStart and SleepDuration on various parameters
  * output as chart (dir [plot/](plot/)) and text file ([sleep_report.txt](report/sleep_report.txt))
* [app.py](src/app.py)
  * interactive visualization
  * start via
  * `streamlit run src/app`

## SonarQube Code Analysis

At [sonarcloud.io](https://sonarcloud.io/summary/overall?id=entorb_analyze-oura&branch=main)
