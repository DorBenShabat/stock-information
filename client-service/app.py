# client-service/app.py

from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

DB_SERVICE_URL = "http://db-service:5001"  # URL for the database service
FETCHER_SERVICE_URL = "http://stock-fetcher-service:5002"  # URL for the stock fetcher service

@app.route('/', methods=['GET', 'POST'])
def index():
    stock_data = None
    error_message = None

    if request.method == 'POST':
        stock_name = request.form.get('stock_name')

        if not stock_name:
            error_message = "Please enter a stock name."
        else:
            # Check if stock data exists in DB
            db_response = requests.get(f"{DB_SERVICE_URL}/stock", params={"name": stock_name})
            
            if db_response.status_code == 404:
                # Fetch data from the stock fetcher service
                fetcher_response = requests.get(f"{FETCHER_SERVICE_URL}/fetch_stock", params={"name": stock_name})
                if fetcher_response.status_code != 200:
                    error_message = "Failed to fetch stock data. Please try again."
                else:
                    stock_data = fetcher_response.json()
            elif db_response.status_code == 200:
                stock_data = db_response.json()
            else:
                error_message = "An error occurred while retrieving the stock data."

    return render_template('index.html', stock_data=stock_data, error_message=error_message)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

