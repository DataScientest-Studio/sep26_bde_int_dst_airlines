import json
from opensky_api import OpenSkyApi, TokenManager
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st

columns = [
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

def convert_iata_to_icao(airport_iata_code: str) -> str:
    """
    Converts iata code to icao code
    :param airport_iata_code
    :return: icao code
    """

    # Find the appropriate icao code for a given iata code
    with open("static/airport_icao_codes.json", 'r') as f:
        all_airport_icao_codes = json.load(f)
    for airport in all_airport_icao_codes.values():
        if airport["iata"] == airport_iata_code:
           return airport["icao"]

    # Raise error if no match found
    raise(ValueError("Invalid iata code"))

def dt_to_unix(year: int, month: int, day: int, hour:int, minute: int) -> int:
    """
    Converts datetime to unix timestamp
    :param year,month,day,hour,minute
    :return: unix timestamp
    """

    # Set the user's timezone
    local_tz = ZoneInfo("Europe/Berlin")

    # Create datetime object
    dt = datetime(year, month, day, hour, minute, tzinfo=local_tz)

    # Return UNIX timestamp
    return int(dt.timestamp())

def unix_to_dt(unix_time: int) -> datetime:
    """Convert a Unix timestamp to a timezone-aware local datetime.
    :param unix_time: unix timestamp
    :return: datetime
    """

    # Set the user's timezone.
    local_tz = ZoneInfo("Europe/Berlin")

    # Convert seconds since the Unix epoch to local date and time.
    return datetime.fromtimestamp(unix_time, tz=local_tz)

def main():
    with OpenSkyApi(token_manager=TokenManager.from_json_file("../../credentials.json")) as api:

        # Get all locations of aircraft in the air at the moment
        states = api.get_states()

        # Iterate the states object and return the first flight found
        if states is not None:
            for state in states.states:
                if not state.on_ground:
                    test_icao24 = state.icao24
                    print(state)
                    break

        # input("Press any key to continue...")

        # Define input parameters
        airport = convert_iata_to_icao("FRA") # e.g. Frankfurt-am-Main International Airport
        begin = dt_to_unix(year=2026, month=10, day=10, hour=12, minute=0)
        end = dt_to_unix(year=2026, month=10, day=10, hour=13, minute=0)
        t = dt_to_unix(year=2026, month=10, day=9, hour=13, minute=0)

        # Get all arrivals at an airport during a specific timeframe.
        arrivals = api.get_arrivals_by_airport(airport=airport, begin=begin, end=end)

        # Get all departures from an airport during a specific timeframe.
        departures = api.get_departures_by_airport(airport=airport, begin=begin, end=end)

        # Get all flights detected during a specific timeframe.
        interval_flights = api.get_flights_from_interval(begin=begin, end=end)

        # # Display first flight found
        # if interval_flights is not None:
        #     for item in interval_flights:
        #         print(item)
        #         break

        # Only proceed if the data is present
        if all(_dict is not None for _dict in [arrivals, departures, interval_flights]):

            arrivals_df = pd.DataFrame([vars(flight) for flight in arrivals], columns=columns)
            departures_df = pd.DataFrame([vars(flight) for flight in departures], columns=columns)
            interval_flights_df = pd.DataFrame([vars(flight) for flight in interval_flights], columns=columns)

        # Data Cleaning
            for df in [arrivals_df, departures_df, interval_flights_df]:
                df["firstSeen"] = df["firstSeen"].apply(unix_to_dt)
                df["lastSeen"] = df["lastSeen"].apply(unix_to_dt)

            st.dataframe(arrivals_df)
            st.dataframe(interval_flights_df)
            st.dataframe(departures_df)

            # Get all flights for one aircraft during a specific timeframe.
            all_aircraft = api.get_flights_by_aircraft(icao24=test_icao24, begin=begin, end=end)

            # Get the flight path for one aircraft at a specific time.
            flight_path = api.get_track_by_aircraft(icao24=test_icao24, t=t)
            coord_points = vars(flight_path)["path"]
            st.write(coord_points)

            # st.write(all_aircraft)
            # st.write(flight_paths)

if __name__ == "__main__":
    main()
