
import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

import json

from pymongo import MongoClient

load_dotenv()

client_id = os.getenv("OPENSKY_CLIENT_ID")
client_secret = os.getenv("OPENSKY_CLIENT_SECRET")

if not client_id or not client_secret:
    raise ValueError("OpenSky login data missing.")

# Requesting token
token_url = (
    "https://auth.opensky-network.org/"
    "auth/realms/opensky-network/protocol/openid-connect/token"
)

token_response = requests.post(
    token_url,
    data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    },
    timeout=30,
)
token_response.raise_for_status()

access_token = token_response.json()["access_token"]

# 2. Get flight
flights_url = "https://opensky-network.org/api/states/all"

params = {
    "lamin": 48.0,
    "lomin": 11.0,
    "lamax": 49.0,
    "lomax": 13.0,
}


flights_response = requests.get(
    flights_url,
    params=params,
    headers=headers,
    timeout=30,
)
flights_response.raise_for_status()

data = flights_response.json()
states = data.get("states") or []


# Transfroming data into list
flights = []

for state in states:
    if state[5] is None or state[6] is None:
        continue

    flight = {
        "icao24": state[0],
        "callsign": state[1].strip() if state[1] else None,
        "origin_country": state[2],
        "longitude": state[5],
        "latitude": state[6],
        "baro_altitude_m": state[7],
        "on_ground": state[8],
        "velocity_m_s": state[9],
        "velocity_kmh": (
            round(state[9] * 3.6, 2)
            if state[9] is not None
            else None
        ),
        "true_track": state[10],
        "retrieved_at": datetime.now(timezone.utc),
    }

    flights.append(flight)


# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Select the database and collection
db = client["opensky_db"]
collection = db["flights"]

# Store flight data in MongoDB
if flights:
    result = collection.insert_many(flights)
    print(f"Successfully stored {len(result.inserted_ids)} flight records.")
else:
    print("No flight data available to store.")

# Close the connection
client.close()


