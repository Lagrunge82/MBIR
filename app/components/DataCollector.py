from typing import Dict

import psycopg2
import yaml

from app.config import POSTGRES_USER, POSTGRES_PASSWORD
from app.utils.modbus import Poller
from app.utils.pydantic.models import Config


class DataCollector:
    def __init__(self):
        self.__config = Config(**self.__config_data)
        self.__poller = Poller(self.__config)

    @property
    def __config_data(self) -> Dict:
        with open('config.yml', "r", encoding='utf8') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as e:
                print(e)

    @property
    def config(self):
        return self.__config

    @property
    def connection(self):
        try:
            db_conf = {'host': 'localhost',
                       # 'host': 'postgres',
                       'port': 54320,
                       'database': 'postgres',
                       'user': POSTGRES_USER,
                       'password': POSTGRES_PASSWORD, }
            return psycopg2.connect(**db_conf)
        except Exception as e:
            print(f'Failed to connect to database: {e}')

    def serve(self, connection):
        if connection:
            query = f"""SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.tables 
                        WHERE table_name = '{self.__config.table}'
                        )
                    """
