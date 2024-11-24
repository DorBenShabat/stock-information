# stock-fetche-service/app.py

import requests
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text

app = Flask(__name__)

# DB connection string
DATABASE_URL = "postgresql://user:pendejo@postgres:5432/stock_db"
# Create connection
engine = create_engine(DATABASE_URL)

# Alpha Vantage API configuration
API_URL = "https://www.alphavantage.co/query"
API_KEY = "SHVEBV1DFMGYT3Y2"

@app.route('/fetch_stock', methods=['GET'])
def fetch_and_store_stock():
    stock_name = request.args.get('name')
    if not stock_name:
        return jsonify({"error": "Stock name is required"}), 400

    # API call
    response = requests.get(API_URL, params={
        "function": "TIME_SERIES_DAILY",
        "symbol": stock_name,
        "apikey": API_KEY
    })
    data = response.json()

    # Check if API response contains the expected data
    if "Time Series (Daily)" not in data:
        return jsonify({"error": "Failed to fetch data"}), 500

    # Extract data from the time series
    time_series = data["Time Series (Daily)"]
    latest_date = next(iter(time_series))
    latest_data = time_series[latest_date]

    # Save Data in DB
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO stocks (name, date, open, high, low, close, volume)
            VALUES (:name, :date, :open, :high, :low, :close, :volume)
            ON CONFLICT (name, date) DO NOTHING
        """), {
            "name": stock_name,
            "date": latest_date,
            "open": latest_data["1. open"],
            "high": latest_data["2. high"],
            "low": latest_data["3. low"],
            "close": latest_data["4. close"],
            "volume": latest_data["5. volume"]
        })

    # Return the stock data
    stock_data = {
        "name": stock_name,
        "date": latest_date,
        "open": latest_data["1. open"],
        "high": latest_data["2. high"],
        "low": latest_data["3. low"],
        "close": latest_data["4. close"],
        "volume": latest_data["5. volume"]
    }

    return jsonify({"stock": stock_data})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002, debug=True)
