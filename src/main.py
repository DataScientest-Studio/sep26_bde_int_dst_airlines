import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from dotenv import load_dotenv
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables from the .env file
load_dotenv()

# Ensure project root is on sys.path so `src.models.train_model` resolves cleanly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

app = FastAPI(
    title="Liora Airlines - Analytics & ML Pipeline API",
    description="API providing flight statistics, continent aggregations, and 7-day flight forecasts",
    version="1.5.0"
)

# Fetch secure environment variables
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "airline-data")
COLLECTION_ARRIVALS = os.getenv("COLLECTION_ARRIVALS", "arrivals")
COLLECTION_DEPARTURES = os.getenv("COLLECTION_DEPARTURES", "departures")

# Neon PostgreSQL connection string
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")


def _compute_next_7_days_forecast(days: int = 7) -> list[dict]:
    """
    Trains/retrieves the arrival model via `train_model()` and runs an hourly
    autoregressive forecast over `days * 24` hours, aggregated into daily totals.
    """
    from src.models.train_model import train_model

    results = train_model()
    model = results["model"]
    previous_count = float(results["last_count"])

    total_hours = days * 24
    future_dates = pd.date_range(
        start=pd.Timestamp.now().normalize() + pd.Timedelta(days=1),
        periods=total_hours,
        freq="h"
    )

    predictions = []
    for timestamp in future_dates:
        x_future = pd.DataFrame([{
            "hour": timestamp.hour,
            "day_of_week": timestamp.day_of_week,
            "month": timestamp.month,
            "day_of_month": timestamp.day,
            "previous_count": previous_count,
        }])

        prediction = max(0.0, float(model.predict(x_future)[0]))
        predictions.append(prediction)
        previous_count = prediction

    forecast_df = pd.DataFrame({
        "datetime": future_dates,
        "predicted_arrivals": predictions,
    })
    forecast_df["date"] = forecast_df["datetime"].dt.date

    daily_forecast = (
        forecast_df.groupby("date", as_index=False)["predicted_arrivals"]
        .sum()
    )
    daily_forecast["predicted_arrivals"] = (
        daily_forecast["predicted_arrivals"].round().astype(int)
    )
    daily_forecast["date"] = pd.to_datetime(daily_forecast["date"]).dt.strftime("%Y-%m-%d")

    return daily_forecast.to_dict(orient="records")


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
                cursor.execute(
                    """
                    SELECT datetime, airport, count
                    FROM departures
                    ORDER BY datetime ASC
                    LIMIT 100;
                    """
                )
                departure_results = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT datetime, airport, count
                    FROM arrivals
                    ORDER BY datetime ASC
                    LIMIT 100;
                    """
                )
                arrival_results = cursor.fetchall()

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


@app.get("/predict/", summary="Predict flight arrivals for FRA over the next 7 days")
def predict_flight_metric(
    days: int = Query(7, ge=1, le=14, description="Forecast horizon in days (default: 7)")
):
    try:
        daily_forecast = _compute_next_7_days_forecast(days=days)
        total_predicted_arrivals = sum(item["predicted_arrivals"] for item in daily_forecast)

        return {
            "status": "success",
            "airport": "FRA",
            "metric": "arrivals",
            "source": "src.models.train_model",
            "horizon_days": days,
            "total_predicted_arrivals": total_predicted_arrivals,
            "daily_forecast": daily_forecast,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate flight forecast: {str(e)}")


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