import asyncio
import asyncpg

from contextlib import asynccontextmanager
from typing import Dict, List


class QueryProcessor:
    __TABLE_EXISTS = 'SELECT EXISTS (SELECT 1 FROM information_schema.tables ' \
                     'WHERE table_name = $1);'
    __COLUMNS = 'SELECT column_name FROM information_schema.columns WHERE table_name = $1;'
    __CREATE_TABLE = 'CREATE TABLE {table_name} ' \
                     '(id SERIAL PRIMARY KEY, datetime TIMESTAMPTZ DEFAULT NOW(), {columns});'
    __ADD_COLUMNS = 'ALTER TABLE {table_name} {columns};'

    def __init__(self, db_config: Dict, table_name: str):
        self.__db_conf = db_config
        self.__tn = table_name

    @property
    @asynccontextmanager
    async def __connection(self):
        conn = await asyncpg.connect(**self.__db_conf)
        try:
            yield conn
        finally:
            await conn.close()

    async def __table_exists(self) -> bool:
        async with self.__connection as conn:
            return await conn.fetchval(self.__TABLE_EXISTS, self.__tn)

    async def __create_table(self, columns: List):
        query = self.__CREATE_TABLE.format(table_name=self.__tn, columns=', '.join(columns))
        async with self.__connection as conn:
            await conn.execute(query)

    async def __columns(self):
        async with self.__connection as conn:
            return [row['column_name'] for row in await conn.fetch(self.__COLUMNS, self.__tn)]

    async def __add_columns(self, columns: List):
        async with self.__connection as conn:
            query = self.__ADD_COLUMNS.format(
                table_name=self.__tn,
                columns=", ".join([f'ADD COLUMN {column}' for column in columns])
            )
            await conn.execute(query)

    async def add_row(self, data: zip):
        columns, values = zip(*data)
        query = 'INSERT INTO {table} ({columns}) VALUES ({values})'.format(
            table=self.__tn,
            columns=', '.join(columns),
            values=', '.join([f'${i + 1}' for i in range(len(values))])
        )
        async with self.__connection as conn:
            await conn.execute(query, *values)

    @property
    def table_exists(self) -> bool:
        return asyncio.run(self.__table_exists())

    @property
    def columns(self) -> List:
        return asyncio.run(self.__columns())

    def create_table(self, columns: List):
        asyncio.run(self.__create_table(columns))

    def add_columns(self, columns: List):
        asyncio.run(self.__add_columns(columns))