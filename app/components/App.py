import asyncio
import json
import re
import time
import logging

from datetime import datetime

import yaml

from typing import Dict, List

from app.config import MB_CONFIG_PATH, DB_CONF
from app.utils.pydantic.models import Config, Device, Register
from app.components.QueryProcessor import QueryProcessor
from app.components.AsyncPoller import AsyncPoller


logger = logging.getLogger('application.logger')


class App:
    def __init__(self):
        self.__c: Config = self.__config
        self.__p = AsyncPoller(devices=self.__c.devices, column_namer=self.__get_column_name)
        self.__q = QueryProcessor(db_config=DB_CONF, table_name=self.__c.table)
        self.__prepare_table()

    @property
    def LOG_LEVEL(self):
        return self.__c.log_level

    def __prepare_table(self):
        if self.__q.table_exists is False:
            # create new table:
            columns = self.__get_columns(active=True)
            self.__q.create_table(columns)
        else:
            # check if all fields are present
            columns = self.__get_columns(active=True, exclude=self.__q.columns)
            if columns:
                # add the ones that are missing
                self.__q.add_columns(columns)

    def __get_columns(self, active: bool = None, exclude: List = None) -> List:
        exclude = [] if exclude is None else exclude
        columns = []
        for device in self.__c.devices:
            if device.active is False:
                continue
            for registers in device.registers:
                for register in registers[1].values():
                    if active is not None and register.active != active:
                        continue
                    data_type = register.type
                    column_name = self.__get_column_name(device, register)
                    if column_name.lower() not in exclude:
                        columns.append(f'{column_name} {data_type}')
        return columns

    @staticmethod
    def __get_column_name(dev: Device, reg: Register) -> str:
        column_name = f'{dev.name}_{reg.name}_{reg.type}'
        return re.sub(r'[ (]', '_', re.sub(r'[)-]', '', column_name))

    @property
    def __config(self) -> Config:
        with open(MB_CONFIG_PATH, "r", encoding='utf8') as config:
            try:
                data: Dict = yaml.safe_load(config)
                if data:
                    return Config(**data)
            except yaml.YAMLError as e:
                logger.critical(str(e))

    async def async_exec(self):
        while True:
            start = time.time()
            result = await self.__p.poll
            await self.__q.add_row(data=result)
            scan_rate = self.__c.scan_rate / 1000
            execution_time = min(time.time() - start, scan_rate)
            logger.debug(f'Execution time: {execution_time}')
            await asyncio.sleep(scan_rate - execution_time)
