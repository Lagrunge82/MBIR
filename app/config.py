import os
from dotenv import load_dotenv

load_dotenv()

MB_CONFIG_PATH = os.getenv('MB_CONFIG_PATH')
MB_LOG_LEVEL = int(os.getenv('MB_LOG_LEVEL'))

POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

DB_CONF = {'host': POSTGRES_HOST, 'database': POSTGRES_DB,
           'user': POSTGRES_USER, 'password': POSTGRES_PASSWORD, }
