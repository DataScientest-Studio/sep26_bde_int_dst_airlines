import os
from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

app = FastAPI(
    title="Liora Airlines - Arrivals & Departures API",
    description="API providing filtered departure, arrival, and statistical flight records from MongoDB Atlas",
    version="1.1.0"
)

# Fetch secure environment variables
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "airline-data")
COLLECTION_ARRIVALS = os.getenv("COLLECTION_ARRIVALS", "arrivals")
COLLECTION_DEPARTURES = os.getenv("COLLECTION_DEPARTURES", "departures")

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

# Helper function to get specific collections
def get_mongo_collection(collection_name: str):
    db = get_db_client()
    if db is None:
        return None
    return db[collection_name]

@app.get("/departures", summary="Get filtered departure flight records")
def get_departures(
    airport_code: str = Query(..., description="Origin airport code (e.g., MUC, BER)"),
    limit: int = Query(50, description="Max number of records to return")
):
    collection = get_mongo_collection(COLLECTION_DEPARTURES)
    if collection is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    
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
    collection = get_mongo_collection(COLLECTION_ARRIVALS)
    if collection is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    
    query = {"estArrivalAirportIATA": airport_code.upper()}
    cursor = collection.find(query, {"_id": 0}).limit(limit)
    records = list(cursor)
    
    return {
        "airport": airport_code.upper(),
        "type": "arrivals",
        "count": len(records),
        "data": records
    }

@app.get("/stats/", summary="Get flight statistical summaries and hourly aggregations")
def get_flight_stats(
    airport_code: str = Query(..., description="Airport code to analyze (e.g., DEN, MUC)")
):
    db = get_db_client()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    
    try:
        code = airport_code.upper()
        arr_collection = db[COLLECTION_ARRIVALS]
        dep_collection = db[COLLECTION_DEPARTURES]
        
        # Scalar document counts
        arrival_count = arr_collection.count_documents({"estArrivalAirportIATA": code})
        departure_count = dep_collection.count_documents({"estDepartureAirportIATA": code})
        
        # Hourly Departures Aggregation pipeline
        departure_pipeline = [
            {"$match": {"estDepartureAirportIATA": code}},
            {
                "$project": {
                    "datetime": {"$toDate": "$firstSeen"},
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
            {"$sort": {"datetime": 1, "airport": 1}},
            {"$limit": 100}
        ]

        # Hourly Arrivals Aggregation pipeline
        arrival_pipeline = [
            {"$match": {"estArrivalAirportIATA": code}},
            {
                "$project": {
                    "datetime": {"$toDate": "$firstSeen"},
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
            {"$sort": {"datetime": 1, "airport": 1}},
            {"$limit": 100}
        ]

        departure_results = list(dep_collection.aggregate(departure_pipeline))
        arrival_results = list(arr_collection.aggregate(arrival_pipeline))

        # Convert datetime objects to ISO format strings for valid JSON response serialization
        for r in departure_results:
            if "datetime" in r and r["datetime"]:
                r["datetime"] = r["datetime"].isoformat()
        for r in arrival_results:
            if "datetime" in r and r["datetime"]:
                r["datetime"] = r["datetime"].isoformat()

        return {
            "status": "success",
            "airport": code,
            "metrics": {
                "arrival_count": arrival_count,
                "departure_count": departure_count,
                "total_volume": arrival_count + departure_count,
                "hourly_departures": departure_results,
                "hourly_arrivals": arrival_results
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute statistics: {str(e)}")

@app.get("/predict/", summary="Run ML inference on flight data")
def predict_flight_metric(
    flight_id: str = Query(..., description="Unique flight identifier or parameters for inference")
):
    return {
        "status": "pending_implementation",
        "flight_id": flight_id,
        "message": "ML prediction functions will be integrated here.",
        "prediction": {
            "delayed": False,
            "probability": 0.0
        }
    }

@app.get("/charts/", summary="Provide pre-aggregated dataset payloads for Streamlit charts")
def get_chart_data(
    airport_code: str = Query(..., description="Airport code for visualization data")
):
    db = get_db_client()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    
    return {
        "status": "pending_implementation",
        "airport": airport_code.upper(),
        "message": "Streamlit visualization data payloads will be returned here.",
        "chart_payload": {
            "labels": [],
            "values": []
        }
    }