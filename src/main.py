import os
from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables from the .env file
load_dotenv()

app = FastAPI(
    title="Liora Airlines - Analytics & ML Pipeline API",
    description="API providing flight statistics and continent aggregations from Neon PostgreSQL",
    version="1.4.0"
)

# Fetch secure environment variables
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "airline-data")
COLLECTION_ARRIVALS = os.getenv("COLLECTION_ARRIVALS", "arrivals")
COLLECTION_DEPARTURES = os.getenv("COLLECTION_DEPARTURES", "departures")

# Neon PostgreSQL connection string
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")

# Helper function to get MongoDB client (for raw records endpoints)
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

# Helper function to get Neon PostgreSQL connection with timeout
def get_neon_connection():
    try:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL is not set in environment variables.")
        conn = psycopg2.connect(
            DATABASE_URL, 
            cursor_factory=RealDictCursor,
            connect_timeout=3
        )
        return conn
    except Exception as e:
        print(f"Neon PostgreSQL Connection Error: {e}")
        return None

@app.get("/departures", summary="Get filtered departure flight records from MongoDB")
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

@app.get("/arrivals", summary="Get filtered arrival flight records from MongoDB")
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

@app.get("/stats/", summary="Get flight statistical summaries from Neon PostgreSQL tables")
def get_flight_stats(
    airport_code: str = Query(None, description="Optional airport code filter (e.g., DEN, MUC)")
):
    conn = get_neon_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Neon Database connection failed.")
    
    try:
        with conn.cursor() as cursor:
            code = airport_code.upper() if airport_code else None
            
            if code:
                # Query departures from Neon matching the specific airport
                cursor.execute(
                    """
                    SELECT datetime, airport, count 
                    FROM departures 
                    WHERE UPPER(airport) = %s 
                    ORDER BY datetime ASC 
                    LIMIT 100;
                    """,
                    (code,)
                )
                departure_results = cursor.fetchall()

                # Query arrivals from Neon matching the specific airport
                cursor.execute(
                    """
                    SELECT datetime, airport, count 
                    FROM arrivals 
                    WHERE UPPER(airport) = %s 
                    ORDER BY datetime ASC 
                    LIMIT 100;
                    """,
                    (code,)
                )
                arrival_results = cursor.fetchall()
            else:
                # Query all departures
                cursor.execute(
                    """
                    SELECT datetime, airport, count 
                    FROM departures 
                    ORDER BY datetime ASC 
                    LIMIT 100;
                    """
                )
                departure_results = cursor.fetchall()

                # Query all arrivals
                cursor.execute(
                    """
                    SELECT datetime, airport, count 
                    FROM arrivals 
                    ORDER BY datetime ASC 
                    LIMIT 100;
                    """
                )
                arrival_results = cursor.fetchall()

            # Convert datetime objects to ISO strings for JSON serialization
            for r in departure_results:
                if r.get("datetime"):
                    r["datetime"] = r["datetime"].isoformat()
            for r in arrival_results:
                if r.get("datetime"):
                    r["datetime"] = r["datetime"].isoformat()

        return {
            "status": "success",
            "source": "Neon PostgreSQL",
            "filter_airport": code if code else "ALL",
            "metrics": {
                "hourly_departures": departure_results,
                "hourly_arrivals": arrival_results
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics from Neon: {str(e)}")
    finally:
        conn.close()

        
@app.get("/stats/continents", summary="Get hourly flight counts grouped by continent from Neon")
def get_continent_traffic():
    """
    Fetches pre-aggregated continent traffic metrics directly from the Neon 'continents_count' table.
    """
    conn = get_neon_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Neon Database connection failed.")
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, hour, africa, asia, europe, north_america, south_america, oceania, antarctica 
                FROM continents_count 
                ORDER BY date ASC, hour ASC 
                LIMIT 100;
                """
            )
            continent_records = cursor.fetchall()

        return {
            "status": "success",
            "source": "Neon PostgreSQL (continents_count)",
            "continent_traffic": continent_records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch continent statistics from Neon: {str(e)}")
    finally:
        conn.close()

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