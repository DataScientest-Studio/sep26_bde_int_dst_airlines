import json
import os

from pymongo import MongoClient
from urllib.parse import quote_plus
import dotenv
from opensky_api import OpenSkyApi, TokenManager
from datetime import datetime
from zoneinfo import ZoneInfo

# Import functions to load data into SQL database
from sql_loader import *

# Load environment variables
dotenv.load_dotenv()
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH") or ""
DB_USERNAME = os.getenv("DB_USERNAME") or ""
DB_PASSWORD = os.getenv("DB_PASSWORD") or ""

# Set which data is to be collected and where to store it "database" or "cache"
COLLECT_DATA = {
    "data": {
        "arrivals": True,
        "departures": True,
        "states": True,
        "intervals": True,
    },
    "destination": "database"
}

def unix_to_dt(unix_time: int) -> datetime:
    """Convert a Unix timestamp to a timezone-aware local datetime.
    :param unix_time: unix timestamp
    :return: datetime
    """

    # Set the user's timezone.
    local_tz = ZoneInfo("Europe/Berlin")

    # Convert seconds since the Unix epoch to local date and time.
    return datetime.fromtimestamp(unix_time, tz=local_tz)

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

def convert_icao_to_iata(airport_icao_code: str) -> str:
    """
    Converts icao code to iata code
    :param airport_icao_code
    :return: iata code
    """

    # Find the appropriate icao code for a given iata code
    with open("static/airport_icao_codes.json", 'r') as f:
        all_airport_icao_codes = json.load(f)
    for airport in all_airport_icao_codes.values():
        if airport["icao"] == airport_icao_code:
           return airport["iata"]

    # Return nothing if not found
    return ""

def dt_to_unix(year: int, month: int, day: int, hour:int, minute: int) -> int:
    """
    Converts datetime to unix timestamp
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

def main() -> None:
    """
    Main function – collect data from api and store in cache or database
    :return:
    """
    with OpenSkyApi(token_manager=TokenManager.from_json_file(CREDENTIALS_PATH)) as api:

        # Define input parameters
        airport = convert_iata_to_icao("FRA") # e.g. Frankfurt-am-Main International Airport
        begin = dt_to_unix(year=2026, month=10, day=10, hour=13, minute=0) # e.g. 10 October 2026, 13:00
        end = dt_to_unix(year=2026, month=10, day=10, hour=14, minute=0) # e.g. 10 October 2026, 14:00

        data = {}

        # Get all locations of aircraft in the air at the moment
        if COLLECT_DATA["data"]["states"]:
            data["states"] = api.get_states()

        # Get all arrivals at an airport during a specific timeframe.
        if COLLECT_DATA["data"]["arrivals"]:
            data["arrivals"] = api.get_arrivals_by_airport(airport=airport, begin=begin, end=end)

        # Get all departures from an airport during a specific timeframe.
        if COLLECT_DATA["data"]["departures"]:
            data["departures"] = api.get_departures_by_airport(airport=airport, begin=begin, end=end)

        # Get all flights detected during a specific timeframe.
        if COLLECT_DATA["data"]["intervals"]:
            data["intervals"] = api.get_flights_from_interval(begin=begin, end=end)

        # Convert OpenSky response objects into dictionaries for JSON and MongoDB
        cleaned_data = {}
        for key, value in data.items():
            if key == "states":
                records = value.states if value is not None else []
            else:
                records = value or []
            cleaned_data[key] = [vars(record) for record in records]

        # Clean data (change date format, remove spaces from callsigns, add iata airport codes)
        for value in cleaned_data.values():
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

        # Store data in the cache
        if COLLECT_DATA["destination"] == "cache":
            for key, documents in cleaned_data.items():
                with open(f"cached_data/{key}.json", "w") as f:
                    json.dump(documents, f, indent=4)

        # Store data in the database
        if COLLECT_DATA["destination"] == "database":

            # Create authentication uri
            uri = (
                "mongodb+srv://"
                f"{quote_plus(DB_USERNAME)}:{quote_plus(DB_PASSWORD)}"
                "@liora-airlines.uad1f8o.mongodb.net/"
            )

            # Connect to MongoDB
            client = MongoClient(uri)

            try:
                # Add the dictionary documents to their matching collections.
                for key, documents in cleaned_data.items():
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
                
            
            # Load data to SQL database
            save_arrivals_sql(cleaned_data)
            save_departures_sql(cleaned_data)
            save_intervals_sql(cleaned_data)
            save_states_sql(cleaned_data)



if __name__ == "__main__":
    main()
