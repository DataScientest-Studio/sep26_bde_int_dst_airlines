
import os
import pandas as pd
import psycopg
from dotenv import load_dotenv

from src.data.get_stats_mongo import departure_df, arrival_df, flights_per_hour_df, hourly_counts_df

load_dotenv()

# Get database url for connection to Neon.
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL is missing from .env")


# Load arrival records from arrivals DataFrame.
def save_arrivals_sql(df):

    # Convert the DataFrame into a list of tuples.
    rows = list(df.itertuples(index=False, name=None))

    # Define the SQL statement.
    insert_sql = """
        INSERT INTO arrivals (count, datetime, airport)
        VALUES (%s, %s, %s)
        ON CONFLICT (datetime, airport) DO NOTHING
    """

    # Connect to Neon and insert the records.
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.executemany(insert_sql, rows)

        print("Succesfully inserted arrivals data.")


# Load departure records from DataFrame.
def save_departures_sql(df):

    # Convert the DataFrame into a list of tuples.
    rows = list(df.itertuples(index=False, name=None))

    # Define the SQL statement.
    insert_sql = """
        INSERT INTO departures (count, datetime, airport)
        VALUES (%s, %s, %s)
        ON CONFLICT (datetime, airport) DO NOTHING
    """

    # Connect to Neon and insert the records.
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.executemany(insert_sql, rows)

        print("Succesfully inserted departures data.")


# Load flight count for continents from DataFrame.
def save_continents_sql(df):

    # Convert the DataFrame into a list of tuples.
    rows = list(df.itertuples(index=False, name=None))

    # Define the SQL statement.
    insert_sql = """
        INSERT INTO continents_count (date, hour, africa, asia, europe, north_america, south_america, oceania, antarctica, total)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (date, hour) DO NOTHING
    """

    # Connect to Neon and insert the records.
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.executemany(insert_sql, rows)

        print("Succesfully inserted continents data.")

# Calling functions to load data into SQL database
save_arrivals_sql(arrival_df)
save_departures_sql(departure_df)
save_continents_sql(hourly_counts_df)
