import altair as alt
import pandas as pd
import streamlit as st


st.set_page_config(page_title="Air Traffic Dashboard", page_icon="✈️", layout="wide")
st.html("<style>[data-testid='stHeaderActionElements'] {display: none;}</style>")  # hide links next to headers

# Temporary example arrival data. Replace with the ingested arrivals dataframe.
ARRIVALS_DF = pd.DataFrame(
    {
        "date_time": [
            "2026-11-05T06:00:00+01:00", "2026-11-05T07:00:00+01:00",
            "2026-11-05T08:00:00+01:00", "2026-11-05T09:00:00+01:00",
            "2026-11-05T10:00:00+01:00", "2026-11-05T11:00:00+01:00",
            "2026-11-05T12:00:00+01:00", "2026-11-05T13:00:00+01:00",
            "2026-11-05T14:00:00+01:00", "2026-11-05T15:00:00+01:00",
            "2026-11-05T16:00:00+01:00", "2026-11-05T17:00:00+01:00",
            "2026-11-05T18:00:00+01:00", "2026-11-05T19:00:00+01:00",
            "2026-11-05T20:00:00+01:00", "2026-11-05T21:00:00+01:00",
            "2026-11-05T09:00:00+01:00", "2026-11-05T14:00:00+01:00",
            "2026-11-05T19:00:00+01:00", "2026-11-05T09:00:00+01:00",
            "2026-11-05T14:00:00+01:00", "2026-11-05T19:00:00+01:00",
            "2026-11-05T09:00:00+01:00", "2026-11-05T14:00:00+01:00",
            "2026-11-05T19:00:00+01:00",
        ],
        "airport": ["FRA"] * 16 + ["MUC"] * 3 + ["HAM"] * 3 + ["BER"] * 3,
        "count": [245, 301, 356, 402, 421, 438, 459, 472, 488, 501, 495, 476, 451, 423, 382, 319, 205, 236, 191, 132, 154, 141, 98, 121, 107],
    }
)

# Temporary example departure data. Replace with the ingested departures dataframe.
DEPARTURES_DF = pd.DataFrame(
    {
        "date_time": [
            "2026-11-05T06:00:00+01:00", "2026-11-05T07:00:00+01:00",
            "2026-11-05T08:00:00+01:00", "2026-11-05T09:00:00+01:00",
            "2026-11-05T10:00:00+01:00", "2026-11-05T11:00:00+01:00",
            "2026-11-05T12:00:00+01:00", "2026-11-05T13:00:00+01:00",
            "2026-11-05T14:00:00+01:00", "2026-11-05T15:00:00+01:00",
            "2026-11-05T16:00:00+01:00", "2026-11-05T17:00:00+01:00",
            "2026-11-05T18:00:00+01:00", "2026-11-05T19:00:00+01:00",
            "2026-11-05T20:00:00+01:00", "2026-11-05T21:00:00+01:00",
            "2026-11-05T09:00:00+01:00", "2026-11-05T14:00:00+01:00",
            "2026-11-05T19:00:00+01:00", "2026-11-05T09:00:00+01:00",
            "2026-11-05T14:00:00+01:00", "2026-11-05T19:00:00+01:00",
            "2026-11-05T09:00:00+01:00", "2026-11-05T14:00:00+01:00",
            "2026-11-05T19:00:00+01:00",
        ],
        "airport": ["FRA"] * 16 + ["MUC"] * 3 + ["HAM"] * 3 + ["BER"] * 3,
        "count": [222, 284, 338, 391, 415, 442, 468, 485, 504, 518, 509, 491, 460, 435, 397, 331, 214, 245, 198, 141, 169, 153, 104, 128, 115],
    }
)

# Temporary example state data. Replace with the ingested states dataframe.
STATES_DF = pd.DataFrame(
    {
        "date_time": [
            "2026-11-05T09:00:00+01:00",
            "2026-11-05T14:00:00+01:00",
            "2026-11-05T19:00:00+01:00",
            "2026-11-06T09:00:00+01:00",
            "2026-11-06T14:00:00+01:00",
            "2026-11-06T19:00:00+01:00",
            "2026-11-07T09:00:00+01:00",
            "2026-11-07T14:00:00+01:00",
            "2026-11-07T19:00:00+01:00",
        ],
        "Europe": [3000, 5600, 4100, 3200, 5900, 4300, 3100, 5750, 4200],
        "North America": [4000, 5200, 3600, 4200, 5400, 3750, 4100, 5300, 3650],
        "Asia": [2800, 3900, 3100, 2900, 4100, 3250, 2850, 4000, 3150],
        "South America": [850, 1200, 950, 870, 1240, 990, 860, 1220, 970],
        "Africa": [780, 1050, 830, 800, 1080, 860, 790, 1060, 840],
        "Oceania": [570, 760, 620, 590, 780, 650, 580, 770, 630],
        "Total Count": [12000, 17710, 13200, 12560, 18500, 13800, 12280, 18100, 13440],
    }
)


CONTINENT_COLUMNS = [
    "Europe",
    "North America",
    "Asia",
    "South America",
    "Africa",
    "Oceania",
]
COMPARISON_HOURS = [9, 14, 19]


def prepare_airport_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Converts airport date/time strings and adds labels for chart axes.
    :param dataframe: Airport arrivals or departures dataframe.
    :results: Dataframe with parsed date/time values and hour labels.
    """
    prepared = dataframe.copy()
    prepared["date_time"] = pd.to_datetime(prepared["date_time"])
    prepared["hour_label"] = prepared["date_time"].dt.strftime("%H:%M")
    return prepared


def hourly_chart(dataframe: pd.DataFrame, title: str) -> alt.Chart:
    """
    Builds an hourly bar chart for a single airport dataset.
    :param dataframe: Airport dataframe for one airport.
    :param title: Chart title.
    :results: Altair hourly bar chart.
    """
    return (
        alt.Chart(dataframe)
        .mark_bar(color="#2a6fbb")
        .encode(
            x=alt.X("hour_label:N", title="Hour", sort=dataframe["hour_label"].tolist()),
            y=alt.Y("count:Q", title="Flights"),
            tooltip=[
                alt.Tooltip("date_time:T", title="Time"),
                alt.Tooltip("count:Q", title="Flights"),
            ],
        )
        .properties(title=title, height=310)
    )


def airport_comparison_chart(dataframe: pd.DataFrame, title: str) -> alt.Chart:
    """
    Builds a grouped airport comparison chart for the three shared hours.
    :param dataframe: Airport arrivals or departures dataframe.
    :param title: Chart title.
    :results: Altair grouped bar chart.
    """
    comparison = dataframe[dataframe["date_time"].dt.hour.isin(COMPARISON_HOURS)]
    return (
        alt.Chart(comparison)
        .mark_bar()
        .encode(
            x=alt.X("hour_label:N", title="Hour", sort=["09:00", "14:00", "19:00"]),
            xOffset="airport:N",
            y=alt.Y("count:Q", title="Flights"),
            color=alt.Color("airport:N", title="Airport"),
            tooltip=[
                alt.Tooltip("airport:N", title="Airport"),
                alt.Tooltip("date_time:T", title="Time"),
                alt.Tooltip("count:Q", title="Flights"),
            ],
        )
        .properties(title=title, height=330)
    )


def continent_data(snapshot: pd.Series) -> pd.DataFrame:
    """
    Converts one wide state snapshot into continent/count rows.
    :param snapshot: One row from the states dataframe.
    :results: Dataframe containing continent names and aircraft counts.
    """
    return pd.DataFrame({"continent": CONTINENT_COLUMNS, "count": [snapshot[name] for name in CONTINENT_COLUMNS]})


def continent_pie_chart(dataframe: pd.DataFrame) -> alt.Chart:
    """
    Builds a pie chart of aircraft counts by continent.
    :param dataframe: Dataframe containing continent names and aircraft counts.
    :results: Altair pie chart.
    """
    return (
        alt.Chart(dataframe)
        .mark_arc(innerRadius=45)
        .encode(
            theta=alt.Theta("count:Q", title="Aircraft"),
            color=alt.Color("continent:N", title="Continent"),
            tooltip=[
                alt.Tooltip("continent:N", title="Continent"),
                alt.Tooltip("count:Q", title="Aircraft"),
            ],
        )
        .properties(title="Planes in the sky by continent", height=350)
    )


def continent_bar_chart(dataframe: pd.DataFrame) -> alt.Chart:
    """
    Builds a bar chart of aircraft counts by continent.
    :param dataframe: Dataframe containing continent names and aircraft counts.
    :results: Altair bar chart.
    """
    return (
        alt.Chart(dataframe.sort_values("count", ascending=False))
        .mark_bar(color="#32a852")
        .encode(
            x=alt.X("count:Q", title="Aircraft"),
            y=alt.Y("continent:N", title="Continent", sort="-x"),
            tooltip=[
                alt.Tooltip("continent:N", title="Continent"),
                alt.Tooltip("count:Q", title="Aircraft"),
            ],
        )
        .properties(title="Planes by continent", height=350)
    )

# Prepare data
ARRIVALS_DF = prepare_airport_data(ARRIVALS_DF)
DEPARTURES_DF = prepare_airport_data(DEPARTURES_DF)
STATES_DF["date_time"] = pd.to_datetime(STATES_DF["date_time"])

# Title and headers
st.title("Air Traffic Dashboard")
st.caption("Sep26_bde_int_dst_airlines: Adam, Clyde, Mythili, Thao")
st.divider()
st.header("Aircraft Departures and Arrivals")
st.write("\n")

############################
######## FRA Stats #########
############################

fra_arrivals = ARRIVALS_DF[ARRIVALS_DF["airport"] == "FRA"]
fra_departures = DEPARTURES_DF[DEPARTURES_DF["airport"] == "FRA"]

hourly_arrivals_column, hourly_departures_column = st.columns(2)
with hourly_arrivals_column:
    st.altair_chart(hourly_chart(fra_arrivals, "Hourly arrivals at FRA"), width="stretch")
with hourly_departures_column:
    st.altair_chart(hourly_chart(fra_departures, "Hourly departures at FRA"), width="stretch")

#############################################
######## FRA/MUC/HAM/BER Comparison #########
#############################################

arrival_comparison_column, departure_comparison_column = st.columns(2)
with arrival_comparison_column:
    st.altair_chart(
        airport_comparison_chart(ARRIVALS_DF, "Arrival comparison: FRA, MUC, HAM, BER"),
        width="stretch",
    )
with departure_comparison_column:
    st.altair_chart(
        airport_comparison_chart(DEPARTURES_DF, "Departure comparison: FRA, MUC, HAM, BER"),
        width="stretch",
    )


###############################
######## States Stats #########
###############################

st.divider()
st.header("Aircraft Locations at a Snapshot in Time")

input_column, detail_column = st.columns([1, 1.5], vertical_alignment="center")
with input_column:
    with st.container(border=True):
        snapshot_options = STATES_DF["date_time"].dt.strftime("%Y-%m-%d %H:%M").tolist()
        snapshot_options_dates = STATES_DF["date_time"].dt.date.tolist()
        snapshot_options_time = STATES_DF["date_time"].dt.strftime("%H:%M").unique().tolist()

        date_column, time_column = st.columns(2)
        with date_column:
            selected_date = st.date_input(
                "Date",
                value=snapshot_options_dates[0],
                min_value=snapshot_options_dates[0],
                max_value=snapshot_options_dates[-1],
            ).strftime("%Y-%m-%d")
        with time_column:
            selected_time = st.selectbox("Time", snapshot_options_time)
        selected_snapshot_label = f"{selected_date} {selected_time}"
        selected_snapshot = STATES_DF.loc[snapshot_options.index(selected_snapshot_label)]
        selected_continents = continent_data(selected_snapshot)
        col_a, col_b, col_c = st.columns([1,5,1])
        with col_b:
            st.markdown(
                f"<h3 style='text-align: center;'>Total Planes: {selected_snapshot['Total Count']:,}</h3>",
                unsafe_allow_html=True,
            )
with detail_column:
    st.dataframe(
        selected_continents.rename(columns={"continent": "Continent", "count": "Aircraft count"}),
        hide_index=True,
        width="stretch",
    )

st.write("\n")
pie_column, continent_bar_column = st.columns(2)
with pie_column:
    st.altair_chart(continent_pie_chart(selected_continents), width="stretch")
with continent_bar_column:
    st.altair_chart(continent_bar_chart(selected_continents), width="stretch")
