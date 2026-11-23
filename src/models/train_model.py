import os
import psycopg
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor


load_dotenv()

# Get database url for connection to Neon.
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL is missing from .env")


# Connect to Neon and fetch data.
conn = create_engine(database_url)

# Load arrivals
arrivals_df = pd.read_sql(
    """
    SELECT *
    FROM arrivals
    WHERE airport = 'FRA'
    ORDER BY datetime
    """,
    conn
)

# Load departures
departures_df = pd.read_sql(
    """
    SELECT *
    FROM departures
    WHERE airport = 'FRA'
    ORDER BY datetime
    """,
    conn
)

conn.dispose()

# Drop duplicates from datasets
arrivals_df = arrivals_df.drop_duplicates(keep="last")
departures_df = departures_df.drop_duplicates(keep="last")

# Transforming data
def transform_data(df):
    df = df.sort_values("datetime").reset_index(drop=True)
    df["hour"] = df["datetime"].dt.hour
    df["day_of_week"] = df["datetime"].dt.day_of_week
    df["month"] = df["datetime"].dt.month
    df["day_of_month"] = df["datetime"].dt.day
    df["previous_count"] = df["count"].shift(1)
    df = df.dropna(subset=["previous_count"]).reset_index(drop=True)

    return df

arrivals_df = transform_data(arrivals_df)
departures_df = transform_data(departures_df)


def train_model():
    # Create model
    model = RandomForestRegressor()

    # Separation into variables and target
    X = arrivals_df[["hour", "day_of_week", "month", "day_of_month", "previous_count"]]
    y = arrivals_df["count"]

    # Split data into training and test dataset
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, shuffle=False)

    # Training model
    model.fit(X_train, y_train)

    # Predict values
    y_pred = model.predict(X_test)

    return {
        "model": model,
        "X_test": X_test,
        "y_test": y_test,
        "y_pred": y_pred,
        "test_dates": arrivals_df.iloc[X_test.index]["datetime"],
        "last_count": arrivals_df["count"].iloc[-1]
    }



