import os
from datetime import datetime
from zoneinfo import ZoneInfo

import dotenv
import pandas as pd
import json
from typing import Tuple
import streamlit as st

st.set_page_config(layout="wide")

dotenv.load_dotenv()
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH")

state_columns = [
    "baro_altitude",
    "callsign",
    "category",
    "geo_altitude",
    "icao24",
    "last_contact",
    "latitude",
    "longitude",
    "on_ground",
    "origin_country",
    "position_source",
    "sensors",
    "spi",
    "squawk",
    "time_position",
    "true_track",
    "velocity",
    "vertical_rate"
]
airport_columns = [
    "arrivalAirportCandidatesCount",
    "callsign",
    "departureAirportCandidatesCount",
    "estArrivalAirport",
    "estArrivalAirportHorizDistance",
    "estArrivalAirportVertDistance",
    "estDepartureAirport",
    "estDepartureAirportHorizDistance",
    "estDepartureAirportVertDistance",
    "firstSeen",
    "icao24",
    "lastSeen"
]

def load_data() -> Tuple[dict,dict,dict,dict]:
    """Load cached aircraft-state and flight records from JSON files.
    :return: States, arrivals, departures, and interval-flight records.
    """
    with open("../data/cached_data/states.json", "r") as f:
        states = json.load(f)

    with open("../data/cached_data/arrivals.json", "r") as f:
        arrivals = json.load(f)

    with open("../data/cached_data/departures.json", "r") as f:
        departures = json.load(f)

    with open("../data/cached_data/intervals.json", "r") as f:
        interval_flights = json.load(f)
    return states, arrivals, departures, interval_flights

def clean_data(states, arrivals, departures, interval_flights) -> Tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    """Convert cached records into cleaned dataframes.
    :param states: Aircraft-state records.
    :param arrivals: Airport-arrival records.
    :param departures: Airport-departure records.
    :param interval_flights: Flight records for the selected time interval.
    :return: State, arrival, departure, and interval-flight dataframes.
    """

    # Only proceed if the data is present
    if all(_dict is not None for _dict in [arrivals, departures, interval_flights, states]):

        arrivals_df = pd.DataFrame([flight for flight in arrivals], columns=airport_columns)
        departures_df = pd.DataFrame([flight for flight in departures], columns=airport_columns)
        interval_flights_df = pd.DataFrame([flight for flight in interval_flights], columns=airport_columns)
        states_df = pd.DataFrame([flight for flight in states], columns=state_columns)

        return states_df, arrivals_df, departures_df, interval_flights_df
    else:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def show_dfs(states_df, arrivals_df, departures_df, interval_flights_df):
    """Display flight dataframes in a two-column Streamlit layout.
    :param states_df: Aircraft-state dataframe.
    :param arrivals_df: Airport-arrivals dataframe.
    :param departures_df: Airport-departures dataframe.
    :param interval_flights_df: Time-interval flights dataframe.
    :return: None.
    """
    left_column, right_column = st.columns(2)

    with left_column:
        st.subheader("Current Aircraft States")
        st.dataframe(states_df)

        st.subheader("Airport Departures")
        st.dataframe(departures_df)

    with right_column:
        st.subheader("Airport Arrivals")
        st.dataframe(arrivals_df)

        st.subheader("Flights in Time Interval")
        st.dataframe(interval_flights_df)

def make_map(states_df: pd.DataFrame) -> None:
    """Display aircraft positions on a Streamlit map.
    :param states_df: Aircraft-state dataframe containing latitude and longitude.
    :return: None.
    """
    # Need to clean Nulls from Lat and Lon
    states_df_cleaned = states_df.dropna(subset=["latitude", "longitude"])
    st.map(states_df_cleaned)

# def main() -> None:
states, arrivals, departures, interval_flights = load_data()
states_df, arrivals_df, departures_df, interval_flights_df = clean_data(states, arrivals, departures, interval_flights)
show_dfs(states_df, arrivals_df, departures_df, interval_flights_df)
make_map(states_df)

# if "__name__" == "__main__":
#     main()

# def calculate_flightpaths():
# if states is not None:
#     for state in states:
#         if not state["on_ground"]:
#             test_icao24 = state["icao24"]
#             pprint(state)
#             break
# with OpenSkyApi(token_manager=TokenManager.from_json_file(CREDENTIALS_PATH)) as api:
#     t = dt_to_unix(year=2026, month=10, day=9, hour=13, minute=0)
#     # Get all flights for one aircraft during a specific timeframe.
#     all_aircraft = api.get_flights_by_aircraft(icao24=test_icao24, begin=begin, end=end)
#
#     # Get the flight path for one aircraft at a specific time.
#     flight_path = api.get_track_by_aircraft(icao24=test_icao24, t=t)
#     coord_points = flight_path)["path"]
#     # st.write(coord_points)
#
#     # st.write(all_aircraft)
#     # st.write(flight_paths)
