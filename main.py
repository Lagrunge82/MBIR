import json
import time
import traceback

import yaml
import psycopg2

from typing import Dict, List

from app.utils.modbus import Poller
from app.utils.pydantic.models import Config
from app.config import POSTGRES_USER, POSTGRES_PASSWORD

data: Dict = {}

with open('app/config.yml', "r", encoding='utf8') as stream:
    try:
        data = yaml.safe_load(stream)
    except yaml.YAMLError as e:
        print(e)

if data:
    config = Config(**data)
    poller = Poller(config)
    poller.connect()

    conn = None
    db_conf = {'host': 'mbir-postgres',
               'database': 'postgres',
               'user': POSTGRES_USER,
               'password': POSTGRES_PASSWORD, }
    try:
        conn = psycopg2.connect(**db_conf)
    except Exception as e:
        print(f'Failed to connect to database: {e}')

    if conn:
        query = f"""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_name = '{config.table}'
            )
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            table_exists = cursor.fetchone()[0]

        formats = {'Signed': 'SMALLINT', 'Unsigned': 'INTEGER',
                   'Hex - ASCII': 'VARCHAR(6)', 'Binary': 'VARCHAR(19)',
                   'Long AB CD': 'BIGINT', 'Long CD AB': 'BIGINT',
                   'Long BA DC': 'BIGINT', 'Long DC BA': 'BIGINT',
                   'Float AB CD': 'REAL', 'Float CD AB': 'REAL',
                   'Float BA DC': 'REAL', 'Float DC BA': 'REAL',
                   'Double AB CD EF GH': 'FLOAT', 'Double GH EF CD AB': 'FLOAT',
                   'Double BA DC FE HG': 'FLOAT', 'Double HG FE DC BA': 'FLOAT', }

        header = []
        if table_exists is False:
            for registers in config.registers:
                for register in registers[1].values():
                    data_type = formats.get(register.format)
                    name = register.name
                    column_name = f'{name}_{register.format.replace(" ", "_").replace("-", "")}'
                    header.append(f'{column_name} {data_type}')
            query = f'CREATE TABLE {config.table} (' \
                    f'id SERIAL PRIMARY KEY, ' \
                    f'datetime TIMESTAMPTZ DEFAULT NOW(), ' \
                    f'{", ".join(header)}' \
                    f');'
        else:
            query = f"SELECT column_name FROM information_schema.columns " \
                    f"WHERE table_name = '{config.table}';"
            with conn.cursor() as cursor:
                cursor.execute(query)
                query = ''
                columns = [result[0].lower() for result in cursor.fetchall()]
                for registers in config.registers:
                    for register in registers[1].values():
                        data_type = formats.get(register.format)
                        name = register.name
                        column_name = f'{name}_{register.format.replace(" ", "_").replace("-", "")}'
                        if column_name.lower() not in columns:
                            header.append(f'ADD COLUMN {column_name} {data_type}')
                if header:
                    query = f'ALTER TABLE {config.table} {", ".join(header)};'
        if query:
            with conn.cursor() as cursor:
                cursor.execute(query)
                conn.commit()
        try:
            while True:
                registers: List = sorted(poller.registers,
                                         key=lambda item: item['name'],
                                         reverse=False)
                print(registers)

                data_columns = []
                values = []
                for register in registers:
                    data_columns.append(
                        f"{register['name'].lower()} "
                        f"{register['format'].lower()}".replace(" ", '_').replace("-", "")
                    )
                    if register['format'] in ['Signed', 'Unsigned',
                                              'Long AB CD', 'Long CD AB',
                                              'Long BA DC', 'Long DC BA']:
                        values.append(int(float(register['value'])))
                    elif register['format'] in ['Float AB CD', 'Float CD AB',
                                                'Float BA DC', 'Float DC BA',
                                                'Double AB CD EF GH', 'Double GH EF CD AB',
                                                'Double BA DC FE HG', 'Double HG FE DC BA']:
                        values.append(float(register['value']))
                    elif register['format'] in ['Hex - ASCII', 'Binary']:
                        values.append(register['value'])
                    else:
                        raise Exception(f'Unknown format {register["format"]}')

                if data_columns and values:
                    query = f'INSERT INTO {config.table} ({", ".join(data_columns)}) ' \
                            f'VALUES ({", ".join(["%s"] * len(data_columns))});'

                    with conn.cursor() as cursor:
                        cursor.execute(query, values)
                        conn.commit()
                time.sleep(config.scan_rate / 1000)
        except (KeyboardInterrupt, Exception) as e:
            if isinstance(e, Exception):
                print(f'Exception was thrown while polling: {e}')
                print(f'{type(e).__name__} occurred, args={str(e.args)}\n{traceback.format_exc()}')
            conn.close()
            poller.disconnect()
else:
    print('Configuration data should be provided')
