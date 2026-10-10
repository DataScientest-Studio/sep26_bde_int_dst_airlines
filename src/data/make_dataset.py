import json
from opensky_api import OpenSkyApi, TokenManager
from datetime import datetime
from zoneinfo import ZoneInfo

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

def time_to_unix(year: int, month: int, day: int, hour:int, minute: int) -> int:
    """
    Converts datetime to unix timestamp
    :param year,month,day,hour,minute
    :return: unix timestamp
    """

    # Set the user's timezone
    local_tz = ZoneInfo("Europe/Berlin")

    # This is more automated, but doesn't handle daylights saving's so, it's less reliable
    # local_tz = datetime.now().astimezone().tzinfo

    # Create datetime object
    dt = datetime(year, month, day, hour, minute, tzinfo=local_tz)

    # Return UNIX timestamp
    return int(dt.timestamp())


def main():

    with OpenSkyApi(token_manager=TokenManager.from_json_file("../../credentials.json")) as api:

        # Get all locations of aircraft in the air at the moment
        states = api.get_states()

        # Iterate the states object and return the first 3 flights found
        if states is not None:
            for state in states.states:
                print(state)
                break

        input("Press any key to continue...")

        # Define input parameters
        airport = convert_iata_to_icao("FRA") # e.g. Frankfurt-am-Main International Airport
        begin = time_to_unix(year=2026, month=10, day=9, hour=12, minute=0)
        end = time_to_unix(year=2026, month=10, day=9, hour=13, minute=0)

        # Find all arrivals at a certain airport during a specific timeframe
        flights = api.get_arrivals_by_airport(airport, begin, end)

        # Display first flight found
        if flights is not None:
            for flight in flights:
                print(flight)
                break

if __name__ == "__main__":
    main()