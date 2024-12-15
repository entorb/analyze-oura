"""
Streamlit App for interactive data visualization.
"""

import datetime as dt
import tomllib
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from report import prep_data_sleep

st.set_page_config(page_title="Oura Sleep Report", page_icon=None, layout="wide")
st.title("Oura Sleep Report")

with (Path("src/config.toml")).open("rb") as f:
    config = tomllib.load(f)
date_start_default = (dt.datetime.now(tz=dt.UTC) - dt.timedelta(weeks=4)).date()


df = prep_data_sleep()
df = df.reset_index()
df = df.drop(columns=["bedtime_end", "bedtime_start", "sleep_phase_5_min"])
df = df.sort_values("day", ascending=False)


col1, col2, col3, col4 = st.columns(4)

sel_start_date = col1.date_input(
    "Start", value=date_start_default, format=config["date_format"]
)
if sel_start_date:
    df = df.query("day >= @sel_start_date")

st.columns(1)

d = {}
for prop in ("score", "start of sleep", "end of sleep", "HR average", "HRV average"):
    d[prop] = {}
    d[prop]["week even"] = df.query("week_even == True")[prop].mean().round(1)  # type: ignore
    d[prop]["week uneven"] = df.query("week_even == False")[prop].mean().round(1)  # type: ignore
    lst = [0, 1, 2, 3, 4]
    d[prop]["weekdays"] = df.query("dayofweek == @lst")[prop].mean().round(1)  # type: ignore
    lst = [5, 6]
    d[prop]["weekend"] = df.query("dayofweek == @lst")[prop].mean().round(1)  # type: ignore
# st.write(d)
df2 = pd.DataFrame.from_dict(d)
st.write(df2.transpose())


col1, col2, col3 = st.columns(3)
sel_week_even = col1.selectbox("Week even.", options=("Even", "Uneven"), index=None)
if sel_week_even:
    if sel_week_even == "Even":
        df = df.query("week_even == True")
    elif sel_week_even == "Uneven":
        df = df.query("week_even == False")

sel_weekend = col2.selectbox("Weekend", options=("Weekday", "Weekend"), index=None)
if sel_weekend:
    if sel_weekend == "Weekday":  # Su-Th
        lst = [0, 1, 2, 3, 4]
    elif sel_weekend == "Weekend":  # Fr-Sa
        lst = [5, 6]
    df = df.query("dayofweek == @lst")


day_map = {"Su": 0, "Mo": 1, "Tu": 2, "Wed": 3, "Th": 4, "Fr": 5, "Sa": 6}
sel_weekday = col3.selectbox("Weekday", options=day_map.keys(), index=None)
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


for prop in ("score", "start of sleep", "sleep total h", "HR average", "HRV average"):
    ymin = df[prop].min()
    ymax = df[prop].max()
    c = base.mark_point(size=100).encode(
        y=alt.Y(prop, scale=alt.Scale(domain=[ymin, ymax])),
    )
    cr = c.transform_regression("day", prop).mark_line(color="grey", strokeDash=[4, 4])
    cl = c.mark_line()
    layers = alt.layer(c, cr, cl)  # .resolve_scale(y="independent")
    st.altair_chart(layers, use_container_width=True)  # type: ignore


c1 = base.mark_line().encode(
    y=alt.Y("sleep total h"),
)
c2 = base.mark_line(color="red").encode(
    y=alt.Y("HRV average"),
)
layers = alt.layer(c1, c2).resolve_scale(y="independent")
st.altair_chart(layers, use_container_width=True)  # type: ignore

c1 = base.mark_line().encode(
    y=alt.Y("sleep total h"),
)
c2 = base.mark_line(color="red").encode(
    y=alt.Y("HR average"),
)
layers = alt.layer(c1, c2).resolve_scale(y="independent")
st.altair_chart(layers, use_container_width=True)  # type: ignore


st.columns(1)

st.subheader("relevant data")
st.dataframe(
    data=df,
    hide_index=True,
    column_config={"day": st.column_config.DateColumn(format=config["date_format"])},
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


st.subheader("all data")
st.dataframe(
    data=df,
    hide_index=True,
    column_config={"day": st.column_config.DateColumn(format=config["date_format"])},
)
