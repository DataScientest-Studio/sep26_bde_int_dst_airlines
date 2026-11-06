import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from pymongo import MongoClient
import pandas as pd

load_dotenv()

username = quote_plus(os.getenv("DB_USERNAME"))
password = quote_plus(os.getenv("DB_PASSWORD"))

client = MongoClient(f"mongodb+srv://{username}:{password}@liora-airlines.uad1f8o.mongodb.net/")

db = client["airline-data"]
departures = db["departures"]
arrivals = db["arrivals"]

departure_results = departures.aggregate([
    {
        "$project": {
            "datetime": {
                "$toDate": "$firstSeen"
            },
            "airport": "$estDepartureAirportIATA"
        }
    },
    {
        "$group": {
            "_id": {
                "datetime": {
                    "$dateTrunc": {
                        "date": "$datetime",
                        "unit": "hour"
                    }
                },
                "airport": "$airport"
            },
            "count": {"$sum": 1}
        }
    },
    {
        "$project": {
            "_id": 0,
            "datetime": "$_id.datetime",
            "airport": "$_id.airport",
            "count": 1
        }
    },
    {
        "$sort": {
            "datetime": 1,
            "airport": 1
        }
    }
])

arrival_results = arrivals.aggregate([
    {
        "$project": {
            "datetime": {
                "$toDate": "$firstSeen"
            },
            "airport": "$estArrivalAirportIATA"
        }
    },
    {
        "$group": {
            "_id": {
                "datetime": {
                    "$dateTrunc": {
                        "date": "$datetime",
                        "unit": "hour"
                    }
                },
                "airport": "$airport"
            },
            "count": {"$sum": 1}
        }
    },
    {
        "$project": {
            "_id": 0,
            "datetime": "$_id.datetime",
            "airport": "$_id.airport",
            "count": 1
        }
    },
    {
        "$sort": {
            "datetime": 1,
            "airport": 1
        }
    }
])


departure_df = pd.DataFrame(list(departure_results))
arrival_df = pd.DataFrame(list(arrival_results))
