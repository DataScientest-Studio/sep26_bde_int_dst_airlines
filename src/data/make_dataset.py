import argparse
import json
import os
import time

from pymongo import MongoClient
import dotenv
from opensky_api import OpenSkyApi, TokenManager
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo


# Load environment variables
dotenv.load_dotenv()
CREDENTIALS_ARRDEP_PATH = os.getenv("CREDENTIALS_ARRDEP_PATH") or ""
CREDENTIALS_STATES_PATH = os.getenv("CREDENTIALS_STATES_PATH") or ""
MONGO_URI = os.getenv("MONGO_URI") or ""

def unix_to_dt(unix_time: int) -> datetime:
    """
    Converts a Unix timestamp to a timezone-aware local datetime.
    :param unix_time: Unix timestamp.
    :return: Timezone-aware datetime.
    """

    # Set the user's timezone.
    local_tz = ZoneInfo("Europe/Berlin")

    # Convert seconds since the Unix epoch to local date and time.
    return datetime.fromtimestamp(unix_time, tz=local_tz)

def convert_iata_to_icao(airport_iata_code: str) -> str:
    """
    Converts an IATA airport code to an ICAO airport code.
    :param airport_iata_code: IATA airport code.
    :return: ICAO airport code.
    """

    # Find the appropriate icao code for a given iata code
    with open("static/airport_icao_codes.json", 'r') as f:
        all_airport_icao_codes = json.load(f)
    for _airport in all_airport_icao_codes.values():
        if _airport["iata"] == airport_iata_code:
           return _airport["icao"]

    # Raise error if no match found
    raise(ValueError("Invalid iata code"))

def convert_icao_to_iata(airport_icao_code: str) -> str:
    """
    Converts an ICAO airport code to an IATA airport code.
    :param airport_icao_code: ICAO airport code.
    :return: IATA airport code.
    """

    # Find the appropriate icao code for a given iata code
    with open("static/airport_icao_codes.json", 'r') as f:
        all_airport_icao_codes = json.load(f)
    for _airport in all_airport_icao_codes.values():
        if _airport["icao"] == airport_icao_code:
           return _airport["iata"]

    # Return nothing if not found
    return ""

def dt_to_unix(year: int, month: int, day: int, hour:int, minute: int) -> int:
    """
    Converts datetime to Unix timestamp.
    :param year: Calendar year.
    :param month: Calendar month, from 1 to 12.
    :param day: Day of the month.
    :param hour: Hour in local time.
    :param minute: Minute in local time.
    :return: Unix timestamp.
    """

    # Set the user's timezone
    local_tz = ZoneInfo("Europe/Berlin")

    # Create datetime object
    dt = datetime(year, month, day, hour, minute, tzinfo=local_tz)

    # Return UNIX timestamp
    return int(dt.timestamp())

def get_and_save_departure_and_arrival_data(
    _airport: str, _begin: int, _end: int
) -> dict[str, Any]:
    """
    Collects arrival and departure data from OpenSky for an airport and time window.
    :param _airport: IATA airport code.
    :param _begin: Start of the requested time window as a Unix timestamp.
    :param _end: End of the requested time window as a Unix timestamp.
    :return: Dictionary containing arrival and departure records.
    """
    with OpenSkyApi(token_manager=TokenManager.from_json_file(CREDENTIALS_ARRDEP_PATH)) as api:

        # Define input parameters
        airport_icao = convert_iata_to_icao(_airport)

        # Get all arrivals and departures at an airport during a specific timeframe.
        arrivals = api.get_arrivals_by_airport(airport=airport_icao, begin=_begin, end=_end)
        departures = api.get_departures_by_airport(airport=airport_icao, begin=_begin, end=_end)
        if arrivals is None or departures is None:
            raise RuntimeError("OpenSky returned no response for arrivals/departures. Your API credits may be exhausted.")
        _data = {"arrivals": arrivals, "departures": departures}
        return _data


def get_and_save_states_data() -> dict[str, Any]:
    """
    Collects the current aircraft states from OpenSky.
    :return: Dictionary containing aircraft-state records.
    """
    with OpenSkyApi(token_manager=TokenManager.from_json_file(CREDENTIALS_STATES_PATH)) as api:

        # Get all locations of aircraft in the air at the moment
        states = api.get_states()
        if states is None:
            raise RuntimeError("OpenSky returned no response for states. Your API credits may be exhausted.")
        return {"states": states}

# def get_and_save_tracks_data():
#     with OpenSkyApi(token_manager=TokenManager.from_json_file(CREDENTIALS_ARRDEP_PATH)) as api:
#
#         icao24 = "39de59"
#
#         # Get the track data for the plane that is currently flying (t=0)
#         track = api.get_track_by_aircraft(icao24=icao24, t=0)
#
#         print(type(track))
#         print(track)
#
#         if track is None:
#             print("No live track was found for this aircraft.")
#         else:
#             from pprint import pprint
#             pprint(vars(track))
#             pprint(track.path)


def clean_data(_data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """
    Converts OpenSky response objects into cleaned dictionary records.
    :param _data: Dictionary containing OpenSky response objects.
    :return: Dictionary containing cleaned records grouped by data type.
    """
    # Convert OpenSky response objects into dictionaries for JSON and MongoDB
    _cleaned_data = {}
    for key, value in _data.items():
        if key == "states":
            records = value.states if value is not None else []
        else:
            records = value or []
        _cleaned_data[key] = [vars(record) for record in records]

    # Clean data (change date format, remove spaces from callsigns, add iata airport codes)
    for value in _cleaned_data.values():
        for item in value:
            # Convert dates
            for field in ["time_position", "last_contact", "firstSeen", "lastSeen"]:
                if item.get(field) is not None:
                    item[field] = unix_to_dt(item[field]).isoformat()
            # Convert callsigns
            if item.get("callsign") is not None:
                item["callsign"] = item["callsign"].strip()
            # Add converted airport codes
            if item.get("estArrivalAirport") is not None:
                item["estArrivalAirportIATA"] = convert_icao_to_iata(item["estArrivalAirport"])
            if item.get("estDepartureAirport") is not None:
                item["estDepartureAirportIATA"] = convert_icao_to_iata(item["estDepartureAirport"])
    return _cleaned_data

def save_data(_destination: str, _cleaned_data: dict[str, list[dict[str, Any]]]) -> None:
    """
    Saves cleaned flight records to the configured cache or databases.
    :param _destination: Where to store the data (cache or database).
    :param _cleaned_data: Dictionary containing cleaned records grouped by data type.
    :return: None.
    """
    # Store data in the cache
    if _destination == "cache":
        for key, documents in _cleaned_data.items():
            with open(f"cached_data/{key}.json", "w") as f:
                json.dump(documents, f, indent=4)

    # Store data in the database
    if _destination == "database":

        # Connect to MongoDB
        if not MONGO_URI:
            raise ValueError("MONGO_URI is missing from .env")
        client = MongoClient(MONGO_URI)

        try:
            # Add the dictionary documents to their matching collections.
            for key, documents in _cleaned_data.items():
                db = client["airline-data"]
                collection = db[key]
                if documents:
                    collection.insert_many(documents)
                else:
                    raise Exception("No documents found to add to the database")

            # Close the connection
            client.close()

        except Exception as e:
            raise Exception("The following error occurred: ", e)


def generate_begin_and_end(_type:str) -> tuple[list[int], list[int]]:
    """
    Generates the start and end timestamps for the OpenSky data request.
    :return: Tuple containing the begin and end Unix timestamps.
    """
    yesterday = datetime.now() - timedelta(days=1)
    month = yesterday.month
    day = yesterday.day
    _begin = []
    _end = []
    if _type == "single":
        for i in range(6,22):
            _begin.append(dt_to_unix(year=2026, month=month, day=day, hour=i, minute=0))
            _end.append(dt_to_unix(year=2026, month=month, day=day, hour=i+1, minute=0))
    elif _type == "multiple":
        for i in [9,14,19]:
            _begin.append(dt_to_unix(year=2026, month=month, day=day, hour=i, minute=0))
            _end.append(dt_to_unix(year=2026, month=month, day=day, hour=i+1, minute=0))
    else:
        raise ValueError("Invalid argument for _type")
    return _begin, _end


if __name__ == "__main__":
    # Collect arguments from the shell command
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", required=True)
    parser.add_argument("--destination", default="database")
    args = parser.parse_args()

    # Collects and saves the states data at the moment it is called
    # Runs at 9:00, 14:00, and 19:00 everyday
    if args.type == "states":
        data = get_and_save_states_data()

    # Collects and saves the arrival and departure data for the previous day
    # Runs at 23:00 everyday
    # Collects hourly data from FRA from 6:00-22:00 and data from BER, MUC, and HAM at 9:00, 14:00, 19:00
    elif args.type == "arrdep":
        # First only the hourly data from FRA from 6:00-22:00
        begin_list, end_list = generate_begin_and_end("single")
        data = {"arrivals": [], "departures": []}
        for begin, end in zip(begin_list, end_list):
            data_tmp = get_and_save_departure_and_arrival_data("FRA", begin, end)
            time.sleep(1)
            print(
                "FRA",
                datetime.fromtimestamp(begin, ZoneInfo("Europe/Berlin")).isoformat(),
                f"arrivals={len(data_tmp['arrivals'])}",
                f"departures={len(data_tmp['departures'])}",
            )
            data["arrivals"].extend(data_tmp["arrivals"])
            data["departures"].extend(data_tmp["departures"])

        # Now the data from BER, MUC, and HAM at 9:00, 14:00, 19:00
        begin_list, end_list = generate_begin_and_end("multiple")
        airports = ["BER", "MUC", "HAM"]
        for begin, end in zip(begin_list, end_list):
            for airport in airports:
                data_tmp = get_and_save_departure_and_arrival_data(airport, begin, end)
                time.sleep(1)
                print(
                    airport,
                    datetime.fromtimestamp(begin, ZoneInfo("Europe/Berlin")).isoformat(),
                    f"arrivals={len(data_tmp['arrivals'])}",
                    f"departures={len(data_tmp['departures'])}",
                )
                data["arrivals"].extend(data_tmp["arrivals"])
                data["departures"].extend(data_tmp["departures"])

    else:
       raise ValueError("Invalid argument for --type")

    cleaned_data = clean_data(data)
    save_data(args.destination, cleaned_data)

    # Save to log
    print(
        f"{datetime.now().astimezone().isoformat()}: "
        f"{sum(len(records) for records in cleaned_data.values())} {args.type} entries added"
    )
    print("====================================================")
