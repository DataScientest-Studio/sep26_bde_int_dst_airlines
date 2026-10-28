import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

username = quote_plus(os.getenv("DB_USERNAME"))
password = quote_plus(os.getenv("DB_PASSWORD"))

client = MongoClient(f"mongodb+srv://{username}:{password}@liora-airlines.uad1f8o.mongodb.net/")

db = client["airline-data"]
departures = db["departures"]
arrivals = db["arrivals"]

departure_results = departures.aggregate([
    {
        "$group": {
            "_id": "$estDepartureAirportIATA",
            "count": {"$sum": 1}
        }
    },
    {
        "$sort": {"count": -1}
    }
])

arrival_results = arrivals.aggregate([
    {
        "$group": {
            "_id": "$estArrivalAirportIATA",
            "count": {"$sum": 1}
        }
    },
    {
        "$sort": {"count": -1}
    }
])


for result in departure_results:
    print(f"{result['_id']}: {result['count']}")

for result in arrival_results:
    print(f"{result['_id']}: {result['count']}")

