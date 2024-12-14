"""
Streamlit App for interactive data visualization.
"""

import datetime as dt
import tomllib
from pathlib import Path

import altair as alt
import streamlit as st

from analyze_v2 import prep_data_sleep

st.set_page_config(page_title="Oura Sleep Report", page_icon=None, layout="wide")
st.title("Oura Sleep Report")

with (Path("src/config.toml")).open("rb") as f:
    config = tomllib.load(f)
date_start_default = (dt.datetime.now(tz=dt.UTC) - dt.timedelta(days=21)).date()


df = prep_data_sleep()
df = df.reset_index()
df = df.drop(columns=["id"])
df = df.sort_values("day", ascending=False)


col1, col2, col3 = st.columns(3)

sel_start_date = col1.date_input(
    "Start", value=date_start_default, format=config["date_format"]
)
if sel_start_date:
    df = df.query(f"day >= '{sel_start_date}'")

sel_weekend = col2.selectbox("Week or Weekend", options=("Su-Th", "Fr-Sa"), index=None)
if sel_weekend:
    if sel_weekend == "Su-Th":
        lst = [0, 1, 2, 3, 4]
    elif sel_weekend == "Fr-Sa":
        lst = [5, 6]

    df = df.query("dayofweek == @lst")


# 0 -> Sunday
sel_weekday = col3.selectbox(
    "Weekday", options=("0", "1", "2", "3", "4", "5", "6"), index=None
)
if sel_weekday:
    df = df.query(f"dayofweek == '{sel_weekday}'")


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


for prop in ("duration of sleep", "HR average", "HRV average"):
    c = base.mark_line().encode(
        y=alt.Y(prop),
    )
    cr = c.transform_regression("day", prop).mark_line(color="grey", strokeDash=[4, 4])
    layers = alt.layer(c, cr)  # .resolve_scale(y="independent")
    st.altair_chart(layers, use_container_width=True)  # type: ignore


c1 = base.mark_line().encode(
    y=alt.Y("duration of sleep"),
)
c2 = base.mark_line(color="red").encode(
    y=alt.Y("HRV average"),
)
layers = alt.layer(c1, c2).resolve_scale(y="independent")
st.altair_chart(layers, use_container_width=True)  # type: ignore

c1 = base.mark_line().encode(
    y=alt.Y("duration of sleep"),
)
c2 = base.mark_line(color="red").encode(
    y=alt.Y("HR average"),
)
layers = alt.layer(c1, c2).resolve_scale(y="independent")
st.altair_chart(layers, use_container_width=True)  # type: ignore


st.columns(1)
st.dataframe(
    data=df,
    hide_index=True,
    column_config={"day": st.column_config.DateColumn(format=config["date_format"])},
)
