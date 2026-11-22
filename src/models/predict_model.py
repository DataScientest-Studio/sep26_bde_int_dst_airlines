import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from src.models.train_model import train_model


# Retrieve model data
results = train_model()

# Create chart for actual vs. predicted data
def curve_chart(results):
    """
    Builds a curve chart that compares the number of flights to predicted number of flights.
    :param results: Trained dataset
    """
    fig, ax = plt.subplots(figsize=(7, 4))

    # Create curve for actual data
    ax.plot(
        results["test_dates"],
        results["y_test"],
        label="Actual"
    )

    # Create curve for predicted data
    ax.plot(
        results["test_dates"],
        results["y_pred"],
        label="Predicted"
    )

    # Configure chart layout
    ax.set_xlabel("Date")
    ax.set_ylabel("Number of arrivals")
    ax.set_title("Actual vs. Predicted Flight Arrivals")
    ax.legend()

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    fig.autofmt_xdate()

    return st.pyplot(fig, use_container_width=False)



# Predict flights of the next 7 days
def predict_week(results):
    """
    Builds a bar chart of predicted flight arrrivals in FRA for the next 7 days.
    :param results: Trained dataset
    """

    # Get model used to train the data
    model = results["model"]
    previous_count = float(results["last_count"])

    # Generate timestamps for the next 168 hours
    future_dates = pd.date_range(
        start=pd.Timestamp.now().normalize() + pd.Timedelta(days=1),
        periods=168,
        freq="h"
    )

    # Predict one hour at a time
    predictions = []

    for timestamp in future_dates:
        X_future = pd.DataFrame([{
            "hour": timestamp.hour,
            "day_of_week": timestamp.day_of_week,
            "month": timestamp.month,
            "day_of_month": timestamp.day,
            "previous_count": previous_count
        }])

        prediction = float(model.predict(X_future)[0])

        # Flight counts cannot be negative
        prediction = max(0, prediction)

        predictions.append(prediction)

        # Use the prediction as input for the next hour
        previous_count = prediction

    # Create hourly forecast DataFrame
    forecast_df = pd.DataFrame({
        "datetime": future_dates,
        "predicted_arrivals": predictions
    })

    # Aggregate hourly predictions into daily totals
    forecast_df["date"] = forecast_df["datetime"].dt.date

    daily_forecast = (
        forecast_df.groupby("date", as_index=False)["predicted_arrivals"]
        .sum()
    )

    daily_forecast["predicted_arrivals"] = (
        daily_forecast["predicted_arrivals"].round().astype(int)
    )

    # Display forecast in Streamlit
    st.subheader("Predicted Number of Flight Arrivals – Next 7 Days")
    daily_forecast["date"] = pd.to_datetime(daily_forecast["date"]).dt.strftime("%d %b %Y")

    st.bar_chart(
        daily_forecast.set_index("date")["predicted_arrivals"],
        y_label="Predicted arrivals",
        x_label="Date",
        height=500,
        width=700
    )

    return st.dataframe(daily_forecast, hide_index=True)
