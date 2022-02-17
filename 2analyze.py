#!/usr/bin/env python3
# by Dr. Torben Menke https://entorb.net
# https://github.com/entorb/analyze-oura

"""
analyze data of Oura daily summaries fetched from Oura Cloud API
fetched data is read from data/
a sleep_report.txt is generated
some charts of correlating data are generated in plot/
"""

import json
import os

import matplotlib.pyplot as plt
import pandas as pd

os.makedirs("plot", exist_ok=True)

# empty file
fh_report = open("sleep_report.txt", mode="w", encoding="utf-8", newline="\n")

# fields: see https://cloud.ouraring.com/docs/sleep


# hypnogram_5min:
# '1' = deep (N3) sleep
# '2' = light (N1 or N2) sleep -
# '3' = REM sleep -
# '4' = awake


def prep_data_sleep() -> pd.DataFrame:
    with open("data/data_raw_sleep.json", mode="r", encoding="utf-8") as fh:
        d_json = json.load(fh)
        d_json = d_json["sleep"]  # drop first level
    # print(d)

    # df = pd.read_json("data_raw.json")
    df = pd.DataFrame.from_dict(d_json)

    # remove time series
    df.drop(columns=["hr_5min", "rmssd_5min", "hypnogram_5min"], inplace=True)

    # convert to date format
    for col in ("summary_date", "bedtime_end", "bedtime_start"):
        df[col] = pd.to_datetime(df[col])

    df["dayofweek"] = df["summary_date"].dt.dayofweek

    # set date as index
    df = df.set_index(["summary_date"])

    df.to_csv(
        "data/data_sleep_orig.tsv",
        sep="\t",
        line_terminator="\n",
    )

    # Adding/calcing some data fields

    df["REM sleep %"] = df["rem"] / df["total"] * 100
    df["deep sleep %"] = df["deep"] / df["total"] * 100
    df["light sleep %"] = df["light"] / df["total"] * 100

    df["start of sleep"] = df["bedtime_start_delta"] / 3600
    # -2 -> 22:00
    # +2 -> 02:00

    df["duration of sleep"] = df["total"] / 3600

    df["efficiency %"] = df["efficiency"] * 100

    df["time to fall asleep"] = df["onset_latency"] / 60

    # df["time to fall asleep"].where(df["time to fall asleep"] > 100, 100, inplace=True)

    df["time awake"] = df["awake"] / 60

    df.drop(
        columns=[
            "bedtime_start_delta",
            "total",
            "efficiency",
            "onset_latency",
            "awake",
        ],
        inplace=True,
    )

    # rename some columns
    df.rename(
        columns={
            "rmssd": "HRV average",
            "hr_average": "HR average",
            "hr_lowest": "HR min",
        },
        inplace=True,
    )

    df.to_csv(
        "data/data_sleep_modified.tsv",
        sep="\t",
        line_terminator="\n",
    )
    return df


def corrlation_tester(df, was, interesting_properties):
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
        d_results.items(), key=lambda item: abs(item[1]), reverse=True
    ):
        s = "%+1.3f : %s" % (d_results[column], column)
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


def plotit(df, was, d_results, l_corr_pos, l_corr_neg):
    colors = ("#1f77b4", "green")
    # colors = ("#1f77b4", "#ff7f0e")
    # from
    # colors = axes[0].lines[0].get_color(), axes[0].right_ax.lines[0].get_color()

    for pos_neg in ("positive", "negative"):
        # pos correlation

        if pos_neg == "positive":
            l = l_corr_pos
        elif pos_neg == "negative":
            l = l_corr_neg

        numplots = len(l)
        fig, axes = plt.subplots(
            nrows=numplots, ncols=1, sharex=True, dpi=100, figsize=(8, numplots * 3)
        )

        fig.suptitle(f"effect of '{was}' is {pos_neg} on ...", color=colors[1])
        i = 0
        for column in l:
            axes[i].set_title(f"{column}: {d_results[column]}", color=colors[0])
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
        fig.set_tight_layout(True)
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


df = prep_data_sleep()

interesting_properties = (
    "duration of sleep",
    "HR average",
    "HR min",
    "HRV average",
    "time to fall asleep",
    "time awake",
    "efficiency %",
    "REM sleep %",
    "deep sleep %",
    "light sleep %",
    "breath_average",
    "restless",
    "temperature_delta",
)


# 1. analize influece of start of sleep
was = "start of sleep"


d_results, l_corr_pos, l_corr_neg = corrlation_tester(
    df=df, was=was, interesting_properties=interesting_properties
)
plotit(df, was, d_results, l_corr_pos, l_corr_neg)


# my results:
# time start sleep up (=later) ->
# total sleep time down
# hr up
# mrssd down
# REM sleep % down

# print("\n")

# 2. analize influece of sleep duration

was = "duration of sleep"


d_results, l_corr_pos, l_corr_neg = corrlation_tester(
    df=df, was=was, interesting_properties=interesting_properties
)
plotit(df, was, d_results, l_corr_pos, l_corr_neg)


fh_report.close()


# scatter plots
fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(8, 6))
axes = df.plot.scatter(
    x="start of sleep",
    y="HR min",
    c="dayofweek",
    colormap="viridis",
)
axes.grid(zorder=0)
plt.savefig(fname=f"plot/scatter1.png", format="png")

exit()
