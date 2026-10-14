import json
from opensky_api import OpenSkyApi, TokenManager
from datetime import datetime
from zoneinfo import ZoneInfo

CREDENTIALS_PATH = "../../credentials2.json"

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

def main() -> None:
    with OpenSkyApi(token_manager=TokenManager.from_json_file(CREDENTIALS_PATH)) as api:

        # Get all locations of aircraft in the air at the moment
        states = api.get_states()
        with open("cached_data/states.json", "w") as f:
            json.dump([vars(state) for state in states.states], f, indent=4)

        # Define input parameters
        airport = convert_iata_to_icao("FRA") # e.g. Frankfurt-am-Main International Airport
        begin = dt_to_unix(year=2026, month=10, day=10, hour=12, minute=0)
        end = dt_to_unix(year=2026, month=10, day=10, hour=13, minute=0)

        # Get all arrivals at an airport during a specific timeframe.
        arrivals = api.get_arrivals_by_airport(airport=airport, begin=begin, end=end)
        with open("cached_data/arrivals.json", "w") as f:
            json.dump([vars(flight) for flight in arrivals] if arrivals is not None else [], f, indent=4)

        # Get all departures from an airport during a specific timeframe.
        departures = api.get_departures_by_airport(airport=airport, begin=begin, end=end)
        with open("cached_data/departures.json", "w") as f:
            json.dump([vars(flight) for flight in departures] if departures is not None else [], f, indent=4)

        # Get all flights detected during a specific timeframe.
        interval_flights = api.get_flights_from_interval(begin=begin, end=end)
        with open("cached_data/interval_flights.json", "w") as f:
            json.dump([vars(flight) for flight in interval_flights] if interval_flights is not None else [], f, indent=4)


if __name__ == "__main__":
    main()
