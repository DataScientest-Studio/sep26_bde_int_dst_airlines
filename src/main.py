import os
from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from dotenv import load_dotenv
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Load environment variables from the .env file
load_dotenv()

app = FastAPI(
    title="Liora Airlines - Analytics & ML Pipeline API",
    description="API providing advanced flight statistics, hourly aggregations, and geographical traffic data from MongoDB Atlas",
    version="1.2.0"
)

# Fetch secure environment variables
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "airline-data")
COLLECTION_ARRIVALS = os.getenv("COLLECTION_ARRIVALS", "arrivals")
COLLECTION_DEPARTURES = os.getenv("COLLECTION_DEPARTURES", "departures")
COLLECTION_STATES = "states"

# Helper function to get database client
def get_db_client():
    try:
        if not MONGO_URI:
            raise ValueError("MONGO_URI is not set in environment variables.")

        client = MongoClient(
            MONGO_URI,
            tls=True,
            tlsInsecure=True,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command('ping')
        return client[DB_NAME]
    except Exception as e:
        print(f"MongoDB Connection Error: {e}")
        return None

@app.get("/departures", summary="Get filtered departure flight records")
def get_departures(
    airport_code: str = Query(..., description="Origin airport code (e.g., MUC, BER)"),
    limit: int = Query(50, description="Max number of records to return")
):
    db = get_db_client()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    
    collection = db[COLLECTION_DEPARTURES]
    query = {"estDepartureAirportIATA": airport_code.upper()}
    cursor = collection.find(query, {"_id": 0}).limit(limit)
    records = list(cursor)
    
    return {
        "airport": airport_code.upper(),
        "type": "departures",
        "count": len(records),
        "data": records
    }

@app.get("/arrivals", summary="Get filtered arrival flight records")
def get_arrivals(
    airport_code: str = Query(..., description="Destination airport code (e.g., LAX, SFO)"),
    limit: int = Query(50, description="Max number of records to return")
):
    db = get_db_client()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    
    collection = db[COLLECTION_ARRIVALS]
    query = {"estArrivalAirportIATA": airport_code.upper()}
    cursor = collection.find(query, {"_id": 0}).limit(limit)
    records = list(cursor)
    
    return {
        "airport": airport_code.upper(),
        "type": "arrivals",
        "count": len(records),
        "data": records
    }

@app.get("/stats/", summary="Get comprehensive flight statistical summaries & script aggregations")
def get_flight_stats(
    airport_code: str = Query(None, description="Optional airport code filter (e.g., DEN, MUC)")
):
    db = get_db_client()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    
    try:
        arr_collection = db[COLLECTION_ARRIVALS]
        dep_collection = db[COLLECTION_DEPARTURES]
        states_collection = db[COLLECTION_STATES]
        
        match_dep = {"estDepartureAirportIATA": airport_code.upper()} if airport_code else {}
        match_arr = {"estArrivalAirportIATA": airport_code.upper()} if airport_code else {}

        # 1. Hourly Departures Aggregation
        dep_pipeline = [
            {"$match": match_dep},
            {"$project": {"datetime": {"$toDate": "$firstSeen"}, "airport": "$estDepartureAirportIATA"}},
            {
                "$group": {
                    "_id": {"datetime": {"$dateTrunc": {"date": "$datetime", "unit": "hour"}}, "airport": "$airport"},
                    "count": {"$sum": 1}
                }
            },
            {"$project": {"_id": 0, "datetime": "$_id.datetime", "airport": "$_id.airport", "count": 1}},
            {"$sort": {"datetime": 1, "airport": 1}},
            {"$limit": 100}
        ]

        # 2. Hourly Arrivals Aggregation
        arr_pipeline = [
            {"$match": match_arr},
            {"$project": {"datetime": {"$toDate": "$firstSeen"}, "airport": "$estArrivalAirportIATA"}},
            {
                "$group": {
                    "_id": {"datetime": {"$dateTrunc": {"date": "$datetime", "unit": "hour"}}, "airport": "$airport"},
                    "count": {"$sum": 1}
                }
            },
            {"$project": {"_id": 0, "datetime": "$_id.datetime", "airport": "$_id.airport", "count": 1}},
            {"$sort": {"datetime": 1, "airport": 1}},
            {"$limit": 100}
        ]

        departure_results = list(dep_collection.aggregate(dep_pipeline))
        arrival_results = list(arr_collection.aggregate(arr_pipeline))

        # Format datetimes for JSON compatibility
        for r in departure_results:
            if "datetime" in r and r["datetime"]:
                r["datetime"] = r["datetime"].isoformat()
        for r in arrival_results:
            if "datetime" in r and r["datetime"]:
                r["datetime"] = r["datetime"].isoformat()

        # 3. Overall Flights Per Hour (from states collection)
        states_pipeline = [
            {"$match": {"on_ground": False, "last_contact": {"$ne": None}, "icao24": {"$ne": None}}},
            {"$group": {"_id": {"date": {"$substr": ["$last_contact", 0, 10]}, "hour": {"$substr": ["$last_contact", 11, 2]}, "icao24": "$icao24"}}},
            {"$group": {"_id": {"date": "$_id.date", "hour": "$_id.hour"}, "flight_count": {"$sum": 1}}},
            {"$sort": {"_id.date": 1, "_id.hour": 1}},
            {"$limit": 100}
        ]
        state_results = list(states_collection.aggregate(states_pipeline))
        flights_per_hour = [
            {"date": r["_id"]["date"], "hour": r["_id"]["hour"], "flight_count": r["flight_count"]}
            for r in state_results
        ]

        return {
            "status": "success",
            "filter_airport": airport_code.upper() if airport_code else "ALL",
            "metrics": {
                "hourly_departures": departure_results,
                "hourly_arrivals": arrival_results,
                "flights_per_hour": flights_per_hour
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute statistics: {str(e)}")

@app.get("/stats/continents", summary="Get hourly flight counts grouped by continent for yesterday")
def get_continent_traffic():
    """
    Executes spatial lookup using Natural Earth boundaries to aggregate 
    yesterday's active airborne flights across continents.
    """
    db = get_db_client()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    
    try:
        states_collection = db[COLLECTION_STATES]
        
        # Load world boundaries
        world = gpd.read_file(
            "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
        )[["CONTINENT", "geometry"]].to_crs("EPSG:4326")

        yesterday = datetime.now(ZoneInfo("Europe/Berlin")).date() - timedelta(days=1)
        start = datetime.combine(yesterday, datetime.min.time(), tzinfo=ZoneInfo("Europe/Berlin"))
        end = start + timedelta(days=1)

        continent_pipeline = [
            {
                "$match": {
                    "last_contact": {"$gte": start.isoformat(), "$lt": end.isoformat()},
                    "on_ground": False,
                    "latitude": {"$ne": None},
                    "longitude": {"$ne": None}
                }
            }
        ]

        records = list(states_collection.aggregate(continent_pipeline))
        if not records:
            return {"status": "success", "date": yesterday.isoformat(), "data": []}

        continent_df = pd.DataFrame(records)
        unique_coords = continent_df[["latitude", "longitude"]].drop_duplicates().copy()

        unique_coords["continent"] = unique_coords.apply(
            lambda row: world[world.geometry.contains(Point(row["longitude"], row["latitude"]))]["CONTINENT"].values[0]
            if not world[world.geometry.contains(Point(row["longitude"], row["latitude"]))].empty
            else "Unknown",
            axis=1
        )

        continent_df = continent_df.merge(unique_coords, on=["latitude", "longitude"], how="left")
        continent_df["date"] = continent_df["last_contact"].str[:10]
        continent_df["hour"] = continent_df["last_contact"].str[11:13]

        hourly_counts = (
            continent_df.groupby(["date", "hour", "continent"])["icao24"]
            .nunique()
            .unstack(fill_value=0)
        )

        continents = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania", "Antarctica"]
        hourly_counts = hourly_counts.reindex(columns=continents, fill_value=0)
        hourly_counts["total"] = hourly_counts.sum(axis=1)
        hourly_counts.columns.name = None
        
        result_df = hourly_counts.reset_index()
        
        return {
            "status": "success",
            "date": yesterday.isoformat(),
            "continent_traffic": result_df.to_dict(orient="records")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute continent statistics: {str(e)}")

@app.get("/predict/", summary="Run ML inference on flight data")
def predict_flight_metric(
    flight_id: str = Query(..., description="Unique flight identifier or parameters for inference")
):
    return {
        "status": "pending_implementation",
        "flight_id": flight_id,
        "message": "ML prediction functions will be integrated here.",
        "prediction": {"delayed": False, "probability": 0.0}
    }

@app.get("/charts/", summary="Provide pre-aggregated dataset payloads for Streamlit charts")
def get_chart_data(
    airport_code: str = Query(..., description="Airport code for visualization data")
):
    return {
        "status": "pending_implementation",
        "airport": airport_code.upper(),
        "message": "Streamlit visualization data payloads will be returned here.",
        "chart_payload": {"labels": [], "values": []}
    }