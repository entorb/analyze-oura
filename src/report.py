# by Dr. Torben Menke https://entorb.net
# https://github.com/entorb/analyze-oura
"""
Analyze data of Oura daily summaries fetched from Oura Cloud API.

fetched data is read from data/
a sleep_report.txt is generated
some charts of correlating data are generated in plot/
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# from turtle import color

# import numpy as np
# import matplotlib.ticker as mtick

Path("plot").mkdir(exist_ok=True)
Path("report").mkdir(exist_ok=True)

# empty file
fh_report = Path("report/sleep_report.txt").open(  # noqa: SIM115
    mode="w",
    encoding="utf-8",
    newline="\n",
)

# fields: see https://cloud.ouraring.com/docs/sleep


# hypnogram_5min:
# '1' = deep (N3) sleep
# '2' = light (N1 or N2) sleep -
# '3' = REM sleep -
# '4' = awake


def get_readiness_data(d: dict, key: str) -> int | None:
    """Extract score and temperature_deviation from readiness subsection."""
    res = None
    if d and key in d:
        value = d.get(key)
        if value:
            if key == "score":
                res = int(value)
            if key == "temperature_deviation":
                res = round(value, 1)
    return res


def prep_data_sleep() -> pd.DataFrame:
    """
    Prepare sleep data.
    """
    with Path("data/data_sleep.json").open(encoding="utf-8") as fh:
        d1 = json.load(fh)
    d1 = d1["data"]  # drop first level

    df = pd.DataFrame.from_dict(d1)

    # filter on sleep period=0
    # df = df[df["period"] == 0]
    # better:
    # filter on >4h sleep
    df = df.query(f"time_in_bed > {4 * 3600}")
    # to prevent SettingWithCopyWarning
    df = df.copy()

    # converting "bedtime_start": "2021-12-30T23:38:05+01:00"
    #  to datetime without timezone (=localtime)
    for col in ("bedtime_end", "bedtime_start"):
        df[col] = pd.to_datetime(df[col], format="ISO8601", utc=True)
        df[col] = df[col].dt.tz_convert(tz="Europe/Berlin")
        df[col] = df[col].dt.tz_localize(None)

    # remove 5min-interval time series
    df = df.drop(columns=["heart_rate", "hrv", "movement_30_sec"])

    # export original data as csv
    df.to_csv(
        path_or_buf="data/data_sleep_orig.tsv",
        sep="\t",
        lineterminator="\n",
    )

    # flatten readiness sub section
    df["score"] = df["readiness"].apply(lambda x: get_readiness_data(x, key="score"))
    df["temperature_deviation"] = df["readiness"].apply(
        lambda x: get_readiness_data(x, key="temperature_deviation")
    )

    # drop more columns
    df = df.drop(columns=["id", "sleep_algorithm_version", "readiness"])

    # DateTime parsing
    df["day"] = pd.to_datetime(df["day"], format="%Y-%m-%d")  # , format="ISO8601"
    df["dayofweek"] = df["day"].dt.dayofweek
    df["week_no"] = df["day"].apply(lambda x: x.isocalendar()[1])
    df["week_even"] = df["week_no"].apply(lambda x: x % 2 == 0)

    #
    # Adding/calculating some data fields
    #
    df["REM sleep %"] = (
        df["rem_sleep_duration"] / df["total_sleep_duration"] * 100
    ).round(1)
    df["deep sleep %"] = (
        df["deep_sleep_duration"] / df["total_sleep_duration"] * 100
    ).round(1)
    df["light sleep %"] = (
        df["light_sleep_duration"] / df["total_sleep_duration"] * 100
    ).round(1)

    # calc start of sleep as seconds since start of day -> decimal hours
    df["start of sleep"] = (
        (
            df["bedtime_start"]
            - df["day"]
            + pd.Timedelta(days=1)  # 1 day offset, since bedtime starts on the prev day
        ).dt.total_seconds()
        / 3600
    ).round(1)
    df["end of sleep"] = (
        df["bedtime_end"].dt.hour + df["bedtime_end"].dt.minute / 60
    ).round(1)

    # df["time to fall asleep"].where(df["time to fall asleep"]
    #                                 > 100, 100, inplace=True)

    # round to 1 digit
    for col in ("average_heart_rate", "average_breath"):
        df[col] = df[col].round(1)

    # sec to min
    for col in ("latency",):
        df[col] = (df[col] / 60).round(1)

    # sec to hour
    for col in (
        "deep_sleep_duration",
        "light_sleep_duration",
        "rem_sleep_duration",
        "total_sleep_duration",
        "time_in_bed",
        "awake_time",
    ):
        df[col] = (df[col] / 3600).round(1)

    # rename some columns
    df = df.rename(
        columns={
            "average_hrv": "HRV average",
            "average_heart_rate": "HR average",
            "lowest_heart_rate": "HR mini",
            "deep_sleep_duration": "sleep deep h",
            "light_sleep_duration": "sleep light h",
            "rem_sleep_duration": "sleep rem h",
            "total_sleep_duration": "sleep total h",
            "time_in_bed": "time in bed h",
            "awake_time": "time awake h",
            "latency": "latency min",
        },
    )

    df.to_csv(
        path_or_buf="data/data_sleep_modified.tsv",
        sep="\t",
        lineterminator="\n",
    )
    # set date as index
    df["day"] = df["day"].dt.date
    df = df.set_index(["day"])
    return df


def correlation_tester(
    df: pd.DataFrame, was: str, interesting_properties: str
) -> tuple[dict, list, list]:
    """
    Tester for Correlations.
    """
    s = f"=== Effect of {was} ==="
    print(s)
    fh_report.write(s + "\n")

    d_results = {}
    max_corr = 0.2

    for column in interesting_properties:
        if column == was:
            continue
        corr = round(df[was].corr(df[column]), 3)
        # print(f"{column}: {corr}")
        d_results[column] = corr

    l_corr_pos = []
    l_corr_neg = []
    l_corr_none = []
    # sort by absolute value
    for column, value in sorted(
        d_results.items(),
        key=lambda item: abs(item[1]),
        reverse=True,
    ):
        s = f"{d_results[column]:+1.3f} : {column}"
        print(s)
        fh_report.write(s + "\n")
        if value >= max_corr:
            l_corr_pos.append(column)
        elif value <= -max_corr:
            l_corr_neg.append(column)
        else:
            l_corr_none.append({column})
    fh_report.write("\n")

    return d_results, l_corr_pos, l_corr_neg


def plot_it(
    df: pd.DataFrame, was: str, d_results: dict, l_corr_pos: list, l_corr_neg: list
) -> None:
    """
    Plot the data.
    """
    colors = ("#1f77b4", "green")
    # colors = ("#1f77b4", "#ff7f0e")
    # from
    # colors = axes[0].lines[0].get_color(), axes[0].right_ax.lines[0].get_color()

    for pos_neg in ("positive", "negative"):
        # pos correlation

        list_of_variables = ()
        if pos_neg == "positive":
            list_of_variables = l_corr_pos
        elif pos_neg == "negative":
            list_of_variables = l_corr_neg

        numplots = len(list_of_variables)
        fig, axes = plt.subplots(
            nrows=numplots,
            ncols=1,
            sharex=True,
            dpi=100,
            figsize=(
                8,
                numplots * 3,
            ),
        )

        fig.suptitle(
            f"effect of '{was}' is {pos_neg} on ...",
            color=colors[1],
        )
        i = 0
        for column in list_of_variables:
            axes[i].set_title(
                f"{column}: {d_results[column]}",
                color=colors[0],
            )
            df[column].plot(
                ax=axes[i],
                linewidth=2.0,
                color=colors[0],
            )
            df[was].plot(
                ax=axes[i],
                linewidth=2.0,
                secondary_y=True,
                color=colors[1],
            )

            # layout
            if pos_neg == "negative":
                axes[i].invert_yaxis()

            # tic color
            axes[i].tick_params(axis="y", colors=colors[0])
            axes[i].right_ax.tick_params(axis="y", colors=colors[1])
            # grid
            axes[i].grid(zorder=0)

            # y labels
            axes[i].set_ylabel(column, color=colors[0])
            axes[i].right_ax.set_ylabel(was, color=colors[1])

            i += 1

        # top tics
        # axes[0].tick_params(
        #     axis="x", bottom=False, top=True, labelbottom=False, labeltop=True
        # )
        axes[i - 1].set_xlabel("")
        fig.set_tight_layout(True)  # type: ignore
        fig.savefig(fname=f"plot/sleep-{was}-{pos_neg}.png", format="png")
        plt.close()

    # # neg correlation
    # numplots = len(l_corr_neg)
    # fig, axes = plt.subplots(
    #     nrows=numplots, ncols=1, sharex=True, dpi=100, figsize=(8, numplots * 3)
    # )

    # fig.suptitle(f"Effect of '{was}' is {pos_neg} on ...")
    # i = 0
    # for column in l_corr_neg:
    #     axes[i].set_title(f"{column}: {d_results[column]}")
    #     df[column].plot(
    #         ax=axes[i],
    #         linewidth=2.0,
    #     )
    #     df[was].plot(
    #         ax=axes[i],
    #         linewidth=2.0,
    #         secondary_y=True,
    #     )
    #     # axes[i].right_ax.invert_yaxis()
    #     if pos_neg == "negative":
    #         axes[i].invert_yaxis()
    #     # tic color
    #     axes[i].tick_params(axis="y", colors=axes[i].lines[0].get_color())
    #     axes[i].right_ax.tick_params(
    #         axis="y", colors=axes[i].right_ax.lines[0].get_color()
    #     )
    #     axes[i].grid(zorder=0)
    #     i += 1
    #     # a = axes[i - 1]

    # # top tics
    # # axes[0].tick_params(
    # #     axis="x", bottom=False, top=True, labelbottom=False, labeltop=True
    # # )
    # axes[i - 1].set_xlabel("")
    # fig.set_tight_layout(True)
    # fig.savefig(fname=f"plot/sleep-{was}-{pos_neg}.png", format="png")
    # plt.close()


if __name__ == "__main__":
    df = prep_data_sleep()

    interesting_properties = (
        "sleep total h",
        "HR average",
        "HR mini",
        "HRV average",
        "latency min",
        "time awake h",
        "efficiency",
        "REM sleep %",
        "deep sleep %",
        "light sleep %",
        "average_breath",
        "restless_periods",
    )

    # 1. analize influence of start of sleep
    was = "start of sleep"

    d_results, l_corr_pos, l_corr_neg = correlation_tester(
        df=df,
        was=was,
        interesting_properties=interesting_properties,  # type: ignore
    )
    plot_it(df, was, d_results, l_corr_pos, l_corr_neg)

    # my results:
    # time start sleep up (=later) ->
    # total sleep time down
    # hr up
    # mrssd down
    # REM sleep % down

    # print("\n")

    # 2. analize influence of sleep duration

    was = "sleep total h"

    d_results, l_corr_pos, l_corr_neg = correlation_tester(
        df=df,
        was=was,
        interesting_properties=interesting_properties,  # type: ignore
    )
    plot_it(df, was, d_results, l_corr_pos, l_corr_neg)

    fh_report.close()

    # scatter plots
    fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(8, 6))
    axes = df.plot.scatter(
        x="start of sleep",
        y="HR mini",
        c="dayofweek",
        colormap="viridis",
    )
    axes.grid(zorder=0)
    plt.savefig(fname="plot/scatter1.png", format="png")
