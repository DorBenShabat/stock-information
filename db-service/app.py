import psycopg2
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# DB connection parameters
DATABASE_CONFIG = {
    "dbname": "stock_db",
    "user": "user",
    "password": "pendejo",
    "host": "postgres",
    "port": 5432,
}

# URL for the stock-fetcher service
FETCHER_SERVICE_URL = "http://stock-fetcher-service:5002/fetch_stock"

@app.route('/stock', methods=['GET'])
def get_stock():
    stock_name = request.args.get('name')
    if not stock_name:
        return jsonify({"error": "Stock name is required"}), 400

    try:
        # Connect to the DB
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cur = conn.cursor()

        # Check if stock data exists in the database
        cur.execute("SELECT name, date, open, high, low, close, volume FROM stocks WHERE name = %s", (stock_name,))
        result = cur.fetchone()

        if result:
            # Return the stock data
            columns = ["name", "date", "open", "high", "low", "close", "volume"]
            stock = dict(zip(columns, result))
            return jsonify({"stock": stock})
        else:
            # Fetch stock data from stock-fetcher-service
            response = requests.get(FETCHER_SERVICE_URL, params={"name": stock_name})
            if response.status_code == 200:
                stock_data = response.json().get("stock")
                if stock_data:
                    # Save the stock data in the database
                    cur.execute("""
                        INSERT INTO stocks (name, date, open, high, low, close, volume)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        stock_data["name"],
                        stock_data["date"],
                        stock_data["open"],
                        stock_data["high"],
                        stock_data["low"],
                        stock_data["close"],
                        stock_data["volume"],
                    ))
                    conn.commit()

                    return jsonify({"stock": stock_data})
                else:
                    return jsonify({"error": "Failed to fetch stock data"}), 500
            else:
                return jsonify({"error": "Failed to fetch stock data"}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
