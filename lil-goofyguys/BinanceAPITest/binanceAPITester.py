import requests
import time
import hmac
import hashlib
from urllib.parse import urlencode
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BinanceAPI:
    def __init__(self, api_key, api_secret):
        if not api_key or not api_secret:
            raise ValueError("API key and secret must be non-empty strings")
        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.BASE_URL = 'https://api.binance.us'
        self.time_offset = 0
        self.rate_limits = {}

    def _get_timestamp(self):
        return int((time.time() * 1000) + self.time_offset)

    def _sign(self, params):
        query_string = urlencode(params)
        signature = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        return signature

    def _handle_response(self, response):
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API request failed: {response.status_code} - {response.text}")
            response.raise_for_status()

    def _update_rate_limits(self, response):
        limits = response.headers.get('X-MBX-USED-WEIGHT-1M')
        if limits:
            self.rate_limits['weight'] = int(limits)
            logger.debug(f"Updated rate limits: {self.rate_limits}")

    def check_server_time(self):
        logger.info("Checking server time...")
        try:
            response = requests.get(f"{self.BASE_URL}/api/v3/time")
            server_time = self._handle_response(response)['serverTime']
            local_time = int(time.time() * 1000)
            self.time_offset = server_time - int(time.time() * 1000)
            logger.info(f"Time offset: {self.time_offset}ms")
        except Exception as e:
            logger.error(f"Error checking server time: {e}")
            raise

    def get_exchange_info(self):
        logger.info("Getting exchange information...")
        try:
            response = requests.get(f"{self.BASE_URL}/api/v3/exchangeInfo")
            self._update_rate_limits(response)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Error getting exchange info: {e}")
            raise

    def get_account_info(self):
        logger.info("Getting account information...")
        try:
            params = {'timestamp': self._get_timestamp()}
            params['signature'] = self._sign(params)
            headers = {'X-MBX-APIKEY': self.API_KEY}
            response = requests.get(f"{self.BASE_URL}/api/v3/account", headers=headers, params=params)
            self._update_rate_limits(response)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            raise

    def place_test_order(self, symbol, side, type, quantity):
        logger.info(f"Placing test order: {symbol} {side} {type} {quantity}")
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': type,
                'quantity': quantity,
                'timestamp': self._get_timestamp()
            }
            params['signature'] = self._sign(params)
            headers = {'X-MBX-APIKEY': self.API_KEY}
            response = requests.post(f"{self.BASE_URL}/api/v3/order/test", headers=headers, params=params)
            self._update_rate_limits(response)
            return self._handle_response(response)
        except Exception as e:
            logger.error(f"Error placing test order: {e}")
            raise

def main():
    # Replace with your actual API key and secret
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_SECRET_KEY')

    binance = BinanceAPI(api_key, api_secret)

    try:
        # Check and adjust for server time
        binance.check_server_time()

        # Get exchange information
        exchange_info = binance.get_exchange_info()
        logger.info(f"Exchange has {len(exchange_info['symbols'])} trading pairs")

        # Get account information
        account_info = binance.get_account_info()
        logger.info(f"Account has {len(account_info['balances'])} balances")

        # Place a test order
        test_order = binance.place_test_order('BTCUSDT', 'BUY', 'MARKET', 0.001)
        logger.info("Test order placed successfully")

        # Check final rate limits
        logger.info(f"Final rate limits: {binance.rate_limits}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error occurred: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
