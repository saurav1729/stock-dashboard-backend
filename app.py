# import yfinance as yf
# from flask import Flask, jsonify
# from flask_cors import CORS
# from concurrent.futures import ThreadPoolExecutor
# import pandas as pd

# app = Flask(__name__)
# CORS(app, origins="http://localhost:3000")  # Allow requests from localhost:3000

# # Define a list of 10 companies (tickers)
# # COMPANIES = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX", "BRK-B", "JPM"]

# # Define a list of 10 Indian companies (tickers)
# COMPANIES = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "SBIN.NS", "BAJFINANCE.NS", "BHARTIARTL.NS"]

# # Create a ThreadPoolExecutor with a specific number of threads
# executor = ThreadPoolExecutor(max_workers=5)  # You can adjust the number of workers as needed

# # Function to fetch data for each stock ticker
# def fetch_stock_data(ticker):
#     try:
#         stock = yf.Ticker(ticker)
#         data = stock.history(period="1d")  # Get today's data
#         print(data)
#         if not data.empty and all(col in data.columns for col in ['Close']):
#             return {
#                 "ticker": ticker,
#                 # "open": data['Open'].iloc[-1],
#                 "close": data['Close'].iloc[-1],
#                 # "low": data['Low'].iloc[-1],
#                 # "high": data['High'].iloc[-1],
#                 # "volume": data['Volume'].iloc[-1]
#             }
#         else:
#             return {
#                 "ticker": ticker,
#                 # "open": None,
#                 "close": None,
#                 # "low": None,
#                 # "high": None,
#                 # "volume": None,
#                 "error": "No valid data available"
#             }
#     except Exception as e:
#         return {
#             "ticker": ticker,
#             # "open": None,
#             "close": None,
#             # "low": None,
#             # "high": None,
#             # "volume": None,
#             "error": f"Error fetching data: {str(e)}"
#         }

# @app.route('/stocks', methods=['GET'])
# def get_stocks():
#     # Submit tasks to the thread pool and collect results
#     futures = [executor.submit(fetch_stock_data, ticker) for ticker in COMPANIES]
#     stock_data = [future.result() for future in futures]
    
#     return jsonify(stock_data)

# if __name__ == '__main__':
#     app.run(debug=True)


import yfinance as yf
from flask import Flask, jsonify
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
CORS(app, origins="http://localhost:3000")  # Allow requests from localhost:3000

# Define a list of 10 Indian companies (tickers)
COMPANIES = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "SBIN.NS", "BAJFINANCE.NS", "BHARTIARTL.NS"]

# Create a ThreadPoolExecutor with a specific number of threads
executor = ThreadPoolExecutor(max_workers=5)  # You can adjust the number of workers as needed

# Function to fetch data for each stock ticker
def fetch_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")  # Get today's data
        if not data.empty and all(col in data.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume']):
            return {
                "ticker": ticker,
                "open": data['Open'].iloc[-1],
                "high": data['High'].iloc[-1],
                "low": data['Low'].iloc[-1],
                "close": data['Close'].iloc[-1],
                "volume": int(data['Volume'].iloc[-1])
            }
        else:
            return {
                "ticker": ticker,
                "open": None,
                "high": None,
                "low": None,
                "close": None,
                "volume": None,
                "error": "No valid data available"
            }
    except Exception as e:
        return {
            "ticker": ticker,
            "open": None,
            "high": None,
            "low": None,
            "close": None,
            "volume": None,
            "error": f"Error fetching data: {str(e)}"
        }

@app.route('/stocks', methods=['GET'])
def get_stocks():
    # Submit tasks to the thread pool and collect results
    futures = [executor.submit(fetch_stock_data, ticker) for ticker in COMPANIES]
    stock_data = [future.result() for future in futures]
    
    return jsonify(stock_data)


@app.route('/historical/<string:ticker>', methods=['GET'])
def get_historical_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="5y")  # Fetch data for the last 5 years
        data.reset_index(inplace=True)  # Convert the index to a column for JSON serialization
        historical_data = data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].to_dict(orient='records')
        return jsonify({"ticker": ticker, "data": historical_data})
    except Exception as e:
        return jsonify({"error": f"Error fetching historical data: {str(e)}"}), 500


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

