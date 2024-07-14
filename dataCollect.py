import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('BINANCE_API_KEY')
secret_key = os.getenv('BINANCE_SECRET_KEY')
