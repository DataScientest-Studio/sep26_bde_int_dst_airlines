
import os
from datetime import datetime

import psycopg
from dotenv import load_dotenv

load_dotenv()

# Get database url for connection to Neon.
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL is missing from .env")


# Load arrival records from the cleaned data.
def save_arrivals_sql(cleaned_data):

    arrivals = cleaned_data.get("arrivals", [])

    if not arrivals:
        return

    insert_sql = """
        INSERT INTO arrivals (
            icao24,
            first_seen,
            est_departure_airport,
            last_seen,
            est_arrival_airport,
            callsign,
            est_departure_airport_horiz_distance,
            est_departure_airport_vert_distance,
            est_arrival_airport_horiz_distance,
            est_arrival_airport_vert_distance,
            departure_airport_candidates_count,
            arrival_airport_candidates_count,
            est_arrival_airport_iata,
            est_departure_airport_iata
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s
        )
    """

    rows = []

    for item in arrivals:
        # Convert ISO 8601 strings into Python datetime objects.
        first_seen = (
            datetime.fromisoformat(item["firstSeen"])
            if item.get("firstSeen") else None
        )
        last_seen = (
            datetime.fromisoformat(item["lastSeen"])
            if item.get("lastSeen") else None
        )

        rows.append((
            item.get("icao24"),
            first_seen,
            item.get("estDepartureAirport"),
            last_seen,
            item.get("estArrivalAirport"),
            item.get("callsign"),
            item.get("estDepartureAirportHorizDistance"),
            item.get("estDepartureAirportVertDistance"),
            item.get("estArrivalAirportHorizDistance"),
            item.get("estArrivalAirportVertDistance"),
            item.get("departureAirportCandidatesCount"),
            item.get("arrivalAirportCandidatesCount"),
            item.get("estArrivalAirportIATA"),
            item.get("estDepartureAirportIATA"),
        ))

    # Connect to Neon and insert the records.
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.executemany(insert_sql, rows)


# Load departure records from the cleaned data.
def save_departures_sql(cleaned_data):
    departures = cleaned_data.get("departures", [])

    if not departures:
        return

    insert_sql = """
        INSERT INTO departures (
            icao24,
            first_seen,
            est_departure_airport,
            last_seen,
            est_arrival_airport,
            callsign,
            est_departure_airport_horiz_distance,
            est_departure_airport_vert_distance,
            est_arrival_airport_horiz_distance,
            est_arrival_airport_vert_distance,
            departure_airport_candidates_count,
            arrival_airport_candidates_count,
            est_arrival_airport_iata,
            est_departure_airport_iata
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s
        )
    """

    rows = []

    for item in departures:
        # Convert ISO 8601 strings into Python datetime objects.
        first_seen = (
            datetime.fromisoformat(item["firstSeen"])
            if item.get("firstSeen") else None
        )
        last_seen = (
            datetime.fromisoformat(item["lastSeen"])
            if item.get("lastSeen") else None
        )

        rows.append((
            item.get("icao24"),
            first_seen,
            item.get("estDepartureAirport"),
            last_seen,
            item.get("estArrivalAirport"),
            item.get("callsign"),
            item.get("estDepartureAirportHorizDistance"),
            item.get("estDepartureAirportVertDistance"),
            item.get("estArrivalAirportHorizDistance"),
            item.get("estArrivalAirportVertDistance"),
            item.get("departureAirportCandidatesCount"),
            item.get("arrivalAirportCandidatesCount"),
            item.get("estArrivalAirportIATA"),
            item.get("estDepartureAirportIATA"),
        ))

    # Connect to Neon and insert the records.
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.executemany(insert_sql, rows)


# Load interval records from cleaned data.
def save_intervals_sql(cleaned_data):
    intervals = cleaned_data.get("intervals", [])

    if not intervals:
        return

    insert_sql = """
        INSERT INTO intervals (
            icao24,
            first_seen,
            est_departure_airport,
            last_seen,
            est_arrival_airport,
            callsign,
            est_departure_airport_horiz_distance,
            est_departure_airport_vert_distance,
            est_arrival_airport_horiz_distance,
            est_arrival_airport_vert_distance,
            departure_airport_candidates_count,
            arrival_airport_candidates_count,
            est_arrival_airport_iata,
            est_departure_airport_iata
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s
        )
    """

    rows = []

    for item in intervals:
        # Convert ISO 8601 strings into Python datetime objects.
        first_seen = (
            datetime.fromisoformat(item["firstSeen"])
            if item.get("firstSeen") else None
        )
        last_seen = (
            datetime.fromisoformat(item["lastSeen"])
            if item.get("lastSeen") else None
        )

        rows.append((
            item.get("icao24"),
            first_seen,
            item.get("estDepartureAirport"),
            last_seen,
            item.get("estArrivalAirport"),
            item.get("callsign"),
            item.get("estDepartureAirportHorizDistance"),
            item.get("estDepartureAirportVertDistance"),
            item.get("estArrivalAirportHorizDistance"),
            item.get("estArrivalAirportVertDistance"),
            item.get("departureAirportCandidatesCount"),
            item.get("arrivalAirportCandidatesCount"),
            item.get("estArrivalAirportIATA"),
            item.get("estDepartureAirportIATA"),
        ))

    # Insert the records into Neon.
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.executemany(insert_sql, rows)


# Load state records from the cleaned data.
def save_states_sql(cleaned_data):
    states = cleaned_data.get("states", [])

    if not states:
        return

    insert_sql = """
        INSERT INTO states (
            icao24,
            callsign,
            origin_country,
            time_position,
            last_contact,
            longitude,
            latitude,
            baro_altitude,
            on_ground,
            velocity,
            true_track,
            vertical_rate,
            sensors,
            geo_altitude,
            squawk,
            spi,
            position_source,
            category
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
    """

    rows = []

    for item in states:
        # Convert ISO 8601 strings into Python datetime objects.
        time_position = (
            datetime.fromisoformat(item["time_position"])
            if item.get("time_position") else None
        )
        last_contact = (
            datetime.fromisoformat(item["last_contact"])
            if item.get("last_contact") else None
        )

        rows.append((
            item.get("icao24"),
            item.get("callsign"),
            item.get("origin_country"),
            time_position,
            last_contact,
            item.get("longitude"),
            item.get("latitude"),
            item.get("baro_altitude"),
            item.get("on_ground"),
            item.get("velocity"),
            item.get("true_track"),
            item.get("vertical_rate"),
            item.get("sensors"),
            item.get("geo_altitude"),
            item.get("squawk"),
            item.get("spi"),
            item.get("position_source"),
            item.get("category"),
        ))

    # Insert the records into Neon.
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.executemany(insert_sql, rows)
