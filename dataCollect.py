import os
import time
from datetime import datetime, timedelta
import requests
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Binance API settings
BASE_URL = "https://api.binance.us/api/v3"
API_KEY = os.getenv('BINANCE_API_KEY')
SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')

print(f"API Key: ...{API_KEY[-5:] if API_KEY else 'None'}")
print(f"Secret Key: ...{SECRET_KEY[-5:] if SECRET_KEY else 'None'}")

def get_binance_data(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    headers = {'X-MBX-APIKEY': API_KEY}
    print(f"Requesting URL: {url}")
    print(f"Params: {params}")
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return None

def get_kline_data(symbol, interval="1h", start_time=None, end_time=None):
    endpoint = "klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1000  # maximum allowed by Binance
    }
    if start_time:
        params['startTime'] = int(start_time.timestamp() * 1000)
    if end_time:
        params['endTime'] = int(end_time.timestamp() * 1000)
    
    data = get_binance_data(endpoint, params)
    return data

def fetch_last_day_data(symbol, interval="1h"):
    end_time = datetime.now()
    start_time = end_time - timedelta(days=1)
    
    print(f"Fetching data for {symbol} from {start_time} to {end_time}")
    
    data = get_kline_data(symbol, interval, start_time, end_time)
    if data:
        print(f"Received {len(data)} data points")
    else:
        print("No data received")
    
    return data

def save_to_csv(data, symbol, interval):
    if not data:
        print("No data to save")
        return
    
    df = pd.DataFrame(data, columns=['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
    df['Open time'] = pd.to_datetime(df['Open time'], unit='ms')
    df['Close time'] = pd.to_datetime(df['Close time'], unit='ms')
    for col in ['Open', 'High', 'Low', 'Close', 'Volume', 'Quote asset volume', 'Taker buy base asset volume', 'Taker buy quote asset volume']:
        df[col] = df[col].astype(float)
    df['Number of trades'] = df['Number of trades'].astype(int)
    
    filename = f"{symbol}_{interval}_last_day.csv"
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

def test_api():
    endpoint = "exchangeInfo"
    response = get_binance_data(endpoint)
    if response and 'symbols' in response:
        print("API is responding correctly")
        return response['symbols']
    else:
        print("API test failed")
        return None

# Main execution
print("Testing API connection...")
symbols = test_api()

if symbols:
    print("Available symbols:")
    for symbol_info in symbols:
        print(symbol_info['symbol'])

symbol = "BTCUSDT"  # Changed from BTCUSD to BTCUSDT
interval = "1h"

print(f"Fetching data for {symbol} at {interval} interval...")
data = fetch_last_day_data(symbol, interval)
if data:
    save_to_csv(data, symbol, interval)
    print(f"Successfully fetched and saved {len(data)} data points")
else:
    print("Failed to fetch data")
