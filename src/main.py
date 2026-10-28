import os
import ssl
from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

app = FastAPI(
    title="Liora Airlines - Arrivals & Departures API",
    description="API providing filtered departure and arrival flight records from MongoDB Atlas",
    version="1.0.0"
)

# Fetch secure environment variables
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "airline-data")
COLLECTION_ARRIVALS = os.getenv("COLLECTION_ARRIVALS", "arrivals")
COLLECTION_DEPARTURES = os.getenv("COLLECTION_DEPARTURES", "departures")

def get_mongo_collection(collection_name: str):
    try:
        if not MONGO_URI:
            raise ValueError("MONGO_URI is not set in environment variables.")
        
        # Initialize MongoClient with standard TLS settings compatible with Atlas
        client = MongoClient(
            MONGO_URI, 
            tls=True,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=5000
        )
        
        # Test connection
        client.admin.command('ping')
        return client[DB_NAME][collection_name]
    except Exception as e:
        print(f"MongoDB Connection Error: {e}")
        return None

@app.get("/departures")
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

@app.get("/arrivals")
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