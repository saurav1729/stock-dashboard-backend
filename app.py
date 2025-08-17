
import yfinance as yf
from flask import Flask, jsonify, request
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Define a list of 10 Indian companies (tickers)
COMPANIES = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS",
    "ICICIBANK.NS", "KOTAKBANK.NS", "SBIN.NS", "BAJFINANCE.NS", "BHARTIARTL.NS",

    # 🚗 Auto
    "MARUTI.NS", "M&M.NS", "TATAMOTORS.NS", "EICHERMOT.NS", "HEROMOTOCO.NS",

    # 🏦 Banks & Financials
    "AXISBANK.NS", "INDUSINDBK.NS", "HDFCLIFE.NS", "BAJAJFINSV.NS",

    # 🏭 Industrials & Infra
    "LT.NS", "ADANIENT.NS", "ADANIPORTS.NS", "ULTRACEMCO.NS", "GRASIM.NS",

    # ⚡ Energy & Power
    "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "ADANIGREEN.NS", "TATAPOWER.NS",

    # 🏢 IT
    "WIPRO.NS", "TECHM.NS", "HCLTECH.NS",

    # 🧴 FMCG & Consumer
    "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS", "TITAN.NS",

    # 🔨 Metals & Materials
    "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "COALINDIA.NS",

    # 💊 Pharma & Healthcare
    "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS"
]

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

WATCHLIST = ["AAPL", "GOOGL", "MSFT", "TSLA"]

@app.route('/watchlist', methods=['GET'])
def get_watchlist():
    # Submit tasks to the thread pool and collect results
    futures = [executor.submit(fetch_stock_data, ticker) for ticker in WATCHLIST]
    stock_data = [future.result() for future in futures]
    
    return jsonify(stock_data)

@app.route('/stocks', methods=['GET'])
def get_stocks():
    # Submit tasks to the thread pool and collect results
    futures = [executor.submit(fetch_stock_data, ticker) for ticker in COMPANIES]
    stock_data = [future.result() for future in futures]
    
    return jsonify(stock_data)


@app.route('/historical/<string:ticker>', methods=['GET'])
def get_historical_data(ticker):
    try:
        time_frame = request.args.get("timeFrame", "5y")
        stock = yf.Ticker(ticker)

        # Handle special cases for intraday/hourly
        if time_frame == "1d":
            data = stock.history(period="1d", interval="1h")   # hourly data for today
        elif time_frame == "1mo":
            data = stock.history(period="1mo", interval="1d")  # daily candles for 1 month
        else:
            data = stock.history(period=time_frame)  # default behavior

        data.reset_index(inplace=True)
        historical_data = data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].to_dict(orient='records')

        return jsonify({"ticker": ticker, "data": historical_data})
    except Exception as e:
        return jsonify({"error": f"Error fetching historical data: {str(e)}"}), 500


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

