# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import talib as ta
from datetime import datetime, timedelta
import numpy as np
from threading import Thread
import time

app = Flask(__name__)
CORS(app)

# Cache for storing real-time data
price_cache = {}
last_update = {}

COMPANIES = {
    'RELIANCE.NS': 'Reliance Industries',
    'TCS.NS': 'Tata Consultancy Services',
    'HDFCBANK.NS': 'HDFC Bank',
    'INFY.NS': 'Infosys',
    'ICICIBANK.NS': 'ICICI Bank',
    'HINDUNILVR.NS': 'Hindustan Unilever',
    'BHARTIARTL.NS': 'Bharti Airtel',
    'KOTAKBANK.NS': 'Kotak Bank',
    'ITC.NS': 'ITC',
    'WIPRO.NS': 'Wipro'
}

def format_number(number):
    """Format large numbers into K, M, B"""
    if number >= 1e9:
        return f"₹{number/1e9:.2f}B"
    elif number >= 1e6:
        return f"₹{number/1e6:.2f}M"
    elif number >= 1e3:
        return f"₹{number/1e3:.2f}K"
    return f"₹{number:.2f}"

def calculate_technical_indicators(df):
    """Calculate technical indicators for the dataset"""
    try:
        # Basic indicators
        df['SMA_20'] = ta.SMA(df['Close'], timeperiod=20)
        df['SMA_50'] = ta.SMA(df['Close'], timeperiod=50)
        df['SMA_200'] = ta.SMA(df['Close'], timeperiod=200)
        df['RSI'] = ta.RSI(df['Close'], timeperiod=14)
        
        # MACD
        df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = ta.MACD(
            df['Close'], fastperiod=12, slowperiod=26, signalperiod=9
        )
        
        # Bollinger Bands
        df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = ta.BBANDS(
            df['Close'], timeperiod=20
        )
        
        # Volume indicators
        df['OBV'] = ta.OBV(df['Close'], df['Volume'])
        
        return df
    except Exception as e:
        print(f"Error calculating indicators: {str(e)}")
        return df

def update_price_cache():
    """Background task to update price cache"""
    while True:
        try:
            for symbol in COMPANIES.keys():
                stock = yf.Ticker(symbol)
                info = stock.info
                
                current_price = info.get('regularMarketPrice', 0)
                prev_close = info.get('previousClose', 0)
                change = ((current_price - prev_close) / prev_close) * 100
                
                price_cache[symbol] = {
                    'name': COMPANIES[symbol],
                    'price': current_price,
                    'change': round(change, 2),
                    'volume': info.get('volume', 0),
                    'market_cap': info.get('marketCap', 0),
                    'high': info.get('dayHigh', 0),
                    'low': info.get('dayLow', 0),
                    'open': info.get('regularMarketOpen', 0)
                }
                
            last_update['timestamp'] = datetime.now()
        except Exception as e:
            print(f"Error updating cache: {str(e)}")
        
        time.sleep(5)  # Update every 5 seconds

# Start background thread for price updates
update_thread = Thread(target=update_price_cache, daemon=True)
update_thread.start()

@app.route('/api/market-status', methods=['GET'])
def get_market_status():
    now = datetime.now()
    market_open = now.hour >= 9 and now.hour < 16  # Simplified market hours
    
    return jsonify({
        'is_open': market_open,
        'last_update': last_update.get('timestamp', now).strftime('%I:%M:%S %p'),
        'next_update': (datetime.now() + timedelta(seconds=5)).strftime('%I:%M:%S %p')
    })

@app.route('/api/stocks', methods=['GET'])
def get_all_stocks():
    try:
        stocks_data = {symbol: {
            **price_cache.get(symbol, {}),
            'symbol': symbol
        } for symbol in COMPANIES.keys()}
        
        return jsonify({
            'stocks': stocks_data,
            'last_update': last_update.get('timestamp', datetime.now()).strftime('%I:%M:%S %p')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_stock_data(symbol):
    try:
        # Get time range from query params, default to '1d'
        timeframe = request.args.get('timeframe', '1d')
        
        # Fetch historical data
        stock = yf.Ticker(symbol)
        df = stock.history(period=timeframe)
        
        # Calculate indicators
        df = calculate_technical_indicators(df)
        
        # Prepare response data
        response_data = {
            'symbol': symbol,
            'name': COMPANIES.get(symbol, 'Unknown'),
            'current': price_cache.get(symbol, {}),
            'historical': {
                'dates': df.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'prices': df['Close'].tolist(),
                'volumes': df['Volume'].tolist(),
            },
            'indicators': {
                'sma20': df['SMA_20'].tolist(),
                'sma50': df['SMA_50'].tolist(),
                'sma200': df['SMA_200'].tolist(),
                'rsi': df['RSI'].tolist(),
                'macd': df['MACD'].tolist(),
                'macd_signal': df['MACD_Signal'].tolist(),
                'macd_hist': df['MACD_Hist'].tolist(),
                'bb_upper': df['BB_Upper'].tolist(),
                'bb_middle': df['BB_Middle'].tolist(),
                'bb_lower': df['BB_Lower'].tolist(),
                'obv': df['OBV'].tolist()
            }
        }
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)