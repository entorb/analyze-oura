"""
Streamlit App for interactive data visualization.
"""

import datetime as dt
import tomllib
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from report import prep_data_sleep


@st.cache_data(ttl="1h")
def read_data() -> pd.DataFrame:
    """Read data (cached)."""
    df = prep_data_sleep()
    df = df.reset_index()
    df = df.drop(columns=["bedtime_end", "bedtime_start", "sleep_phase_5_min"])
    df = df.sort_values("day", ascending=False)
    return df


@st.cache_data(ttl="1h")
def calc_summaries(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate summaries."""
    d = {}
    for prop in (
        "score",
        "start of sleep",
        "end of sleep",
        "HR average",
        "HRV average",
    ):
        d[prop] = {}
        d[prop]["week even"] = df.query("week_even == True")[prop].mean().round(1)  # type: ignore
        d[prop]["week uneven"] = df.query("week_even == False")[prop].mean().round(1)  # type: ignore
        _lst = [0, 1, 2, 3, 4]
        d[prop]["weekdays"] = df.query("dayofweek == @_lst")[prop].mean().round(1)  # type: ignore
        _lst = [5, 6]
        d[prop]["weekend"] = df.query("dayofweek == @_lst")[prop].mean().round(1)  # type: ignore
    df2 = pd.DataFrame.from_dict(d).transpose()
    return df2


def main() -> None:  # noqa: C901, D103, PLR0915
    st.set_page_config(page_title="Oura Sleep Report", page_icon=None, layout="wide")
    st.title("Oura Sleep Report")

    with (Path("src/config.toml")).open("rb") as f:
        config = tomllib.load(f)
    date_start_default = (dt.datetime.now(tz=dt.UTC) - dt.timedelta(weeks=4)).date()

    df = read_data()

    cols = st.columns((1, 3))

    sel_start_date = cols[0].date_input(
        "Start", value=date_start_default, format=config["date_format"]
    )
    if sel_start_date:
        df = df.query("day >= @sel_start_date")

    st.columns(1)
    df2 = calc_summaries(df)

    st.write(df2)

    cols = st.columns(3)
    sel_week_even = cols[0].selectbox("Weeks", options=("Even", "Uneven"), index=None)
    if sel_week_even:
        if sel_week_even == "Even":
            df = df.query("week_even == True")
        elif sel_week_even == "Uneven":
            df = df.query("week_even == False")

    sel_weekend = cols[1].selectbox(
        "Weekend", options=("Weekday", "Weekend"), index=None
    )
    if sel_weekend:
        if sel_weekend == "Weekday":  # Su-Th
            _lst = [0, 1, 2, 3, 4]
        elif sel_weekend == "Weekend":  # Fr-Sa
            _lst = [5, 6]
        df = df.query("dayofweek == @_lst")

    day_map = {"Su": 0, "Mo": 1, "Tu": 2, "Wed": 3, "Th": 4, "Fr": 5, "Sa": 6}
    sel_weekday = cols[2].selectbox("Weekday", options=day_map.keys(), index=None)
    if sel_weekday:
        df = df.query(f"dayofweek == {day_map[sel_weekday]}")

    # c = st.line_chart(data=df, x="day", y="duration of sleep", x_label=None)
    # corresponds to
    # c1 = (
    #     alt.Chart(df)
    #     .mark_line()
    #     .encode(
    #         x=alt.X("day", title=None),
    #         y=alt.Y("duration of sleep"),
    #     )
    # )

    base = alt.Chart(df).encode(alt.X("day", title=None))

    x = df["day"].map(lambda d: (d - df["day"].iloc[0]).days)
    for prop in (
        "score",
        "start of sleep",
        "sleep total h",
        "HR average",
        "HRV average",
    ):
        st.subheader(prop)
        ymin = df[prop].min()
        ymax = df[prop].max()
        mean: float = df[prop].mean()
        y = df[prop].to_numpy()
        slope, _intercept = np.polyfit(x, y, 1)  # type: ignore
        slope = 100.0 * slope / mean if not np.isnan(slope) else 0
        del (y, _intercept)

        c = base.mark_point(size=100).encode(
            y=alt.Y(prop, scale=alt.Scale(domain=[ymin, ymax])),
        )
        reg_line = c.transform_regression("day", prop).mark_line(
            color="gray", strokeDash=[4, 4]
        )
        layers = alt.layer(
            c, c.mark_line(), reg_line
        )  # .resolve_scale(y="independent")
        cols = st.columns((5, 1))
        cols[0].altair_chart(layers, width="stretch")  # type: ignore

        cols[1].metric(
            label="Mean",
            value=f"{mean:.1f}",
            delta=f"{slope:.3f}%",
            label_visibility="visible",
        )

    st.header("Relations")
    y1 = "sleep total h"
    for y2 in ("HR average", "HRV average"):
        st.subheader(f"{y1} <=> {y2}")

        c1 = base.mark_line().encode(
            y=alt.Y(y1),
        )
        c2 = base.mark_line(color="red").encode(
            y=alt.Y(y2),
        )
        layers = alt.layer(c1, c2).resolve_scale(y="independent")
        st.altair_chart(layers, width="stretch")  # type: ignore

    st.columns(1)

    st.header("Raw data")

    st.subheader("Relevant columns")
    st.dataframe(
        data=df,
        hide_index=True,
        column_config={
            "day": st.column_config.DateColumn(format=config["date_format"])
        },
        column_order=[
            "day",
            "start of sleep",
            "end of sleep",
            "score",
            "HR mini",
            "HR average",
            "HRV average",
            "time in bed h",
            "sleep total h",
            "sleep rem h",
            "sleep deep h",
            "temperature_deviation",
        ],
    )

    st.subheader("All data")
    st.dataframe(
        data=df,
        hide_index=True,
        column_config={
            "day": st.column_config.DateColumn(format=config["date_format"])
        },
    )


if __name__ == "__main__":
    main()
