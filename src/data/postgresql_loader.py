
import os
from datetime import datetime

import psycopg
from dotenv import load_dotenv

load_dotenv()

def save_arrivals_sql(cleaned_data):
    # Get arrival records from the cleaned data.
    arrivals = cleaned_data.get("arrivals", [])

    if not arrivals:
        print("No arrival records found. Nothing to insert.")
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
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL is missing from .env")

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.executemany(insert_sql, rows)

    print(f"Inserted {len(rows)} arrivals into Neon.")
