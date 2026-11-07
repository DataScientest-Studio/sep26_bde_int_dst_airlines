import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from pymongo import MongoClient
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

load_dotenv()

username = quote_plus(os.getenv("DB_USERNAME"))
password = quote_plus(os.getenv("DB_PASSWORD"))

client = MongoClient(f"mongodb+srv://{username}:{password}@liora-airlines.uad1f8o.mongodb.net/")

db = client["airline-data"]
departures = db["departures"]
arrivals = db["arrivals"]
states = db["states"]

# Getting departures and arrivals per hour
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

#Getting flights per hour
pipeline = [
    {
        "$match": {
            "on_ground": False,
            "last_contact": {"$ne": None},
            "icao24": {"$ne": None}
        }
    },
    {
        "$group": {
            "_id": {
                "date": {"$substr": ["$last_contact", 0, 10]},
                "hour": {"$substr": ["$last_contact", 11, 2]},
                "icao24": "$icao24"
            }
        }
    },
    {
        "$group": {
            "_id": {
                "date": "$_id.date",
                "hour": "$_id.hour"
            },
            "flight_count": {"$sum": 1}
        }
    },
    {
        "$sort": {
            "_id.date": 1,
            "_id.hour": 1
        }
    }
]

results = list(states.aggregate(pipeline))

flights_per_hour_df = pd.DataFrame([
    {
        "date": r["_id"]["date"],
        "hour": r["_id"]["hour"],
        "flight_count": r["flight_count"]
    }
    for r in results
])


# Getting flights per continent
world = gpd.read_file(
    "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
)

world = world[["CONTINENT", "geometry"]]

world = world.to_crs("EPSG:4326")

yesterday = datetime.now(ZoneInfo("Europe/Berlin")).date() - timedelta(days=1)


start = datetime.combine(yesterday, datetime.min.time(), tzinfo=ZoneInfo("Europe/Berlin"))
end = start + timedelta(days=1)


continent_pipeline = [
    {
        "$match": {
            "last_contact": {
                "$gte": start.isoformat(),
                "$lt": end.isoformat()
            },
            "on_ground": False,
            "latitude": {"$ne": None},
            "longitude": {"$ne": None}
        }
    }
]

records = list(states.aggregate(continent_pipeline))

continent_df = pd.DataFrame(records)

unique_coordinates = continent_df[["latitude", "longitude"]].drop_duplicates()

unique_coordinates = unique_coordinates.copy()

unique_coordinates["continent"] = unique_coordinates.apply(
    lambda row: world[
        world.geometry.contains(Point(row["longitude"], row["latitude"]))
    ]["CONTINENT"].values[0]
    if not world[
        world.geometry.contains(Point(row["longitude"], row["latitude"]))
    ].empty
    else "Unknown",
    axis=1
)

continent_df = continent_df.merge(
    unique_coordinates,
    on=["latitude", "longitude"],
    how="left"
)

continent_df["date"] = continent_df["last_contact"].str[:10]
continent_df["hour"] = continent_df["last_contact"].str[11:13]

hourly_counts = (
    continent_df.groupby(["date", "hour", "continent"])["icao24"]
    .nunique()
    .unstack(fill_value=0)
)

continents = [
    "Africa",
    "Asia",
    "Europe",
    "North America",
    "South America",
    "Oceania",
    "Antarctica"
]

hourly_counts = hourly_counts.reindex(columns=continents, fill_value=0)

hourly_counts["total"] = hourly_counts.sum(axis=1)
hourly_counts.columns.name = None
hourly_counts_df = hourly_counts.reset_index()

