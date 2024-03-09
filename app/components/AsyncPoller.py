import asyncio
import logging
import time
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from itertools import chain
from typing import List, Callable, Dict, Union, Optional, AsyncIterator, Tuple, Any

from pymodbus.client import AsyncModbusTcpClient as TcpClient
from pymodbus.client import AsyncModbusSerialClient as SerialClient
from pymodbus.exceptions import ConnectionException, ModbusIOException

from app.utils.pydantic.models import Device
from app.utils.coders import Decoder, Encoder


logger = logging.getLogger('application.logger')


class AsyncPoller:
    __clients = {}
    __fn = {'DO': 1, 'DI': 2, 'AO': 3, 'AI': 4, }
    __data_len = {'Signed': 1, 'Unsigned': 1,
                  'Hex - ASCII': 1, 'Binary': 1,
                  'Long AB CD': 2, 'Long CD AB': 2,
                  'Long BA DC': 2, 'Long DC BA': 2,
                  'Float AB CD': 2, 'Float CD AB': 2,
                  'Float BA DC': 2, 'Float DC BA': 2,
                  'Double AB CD EF GH': 4, 'Double GH EF CD AB': 4,
                  'Double BA DC FE HG': 4, 'Double HG FE DC BA': 4, }

    def __init__(self, devices: List[Device], column_namer: Callable):
        self.__devices = devices
        self.__column_namer = column_namer
        self.__init_clients()

    def __init_clients(self) -> None:
        for dev in self.__devices:
            if dev.active is False or dev.connection.src in self.__clients:
                continue
            match dev.connection.transport:
                case 'TCP':
                    client = TcpClient(**dev.connection.tcp)
                case 'serial':
                    client = SerialClient(**dev.connection.serial)
                case _:
                    logger.error(f'Unknown transport `{dev.connection.transport}`')
            self.__clients[dev.connection.src] = client

    @staticmethod
    def __format_dict(obj: Union[Decoder, Encoder]) -> Dict:
        return {'Signed': obj.signed, 'Unsigned': obj.unsigned,
                'Hex - ASCII': obj.hex_ascii, 'Binary': obj.binary,
                'Long AB CD': obj.long_ab_cd, 'Long CD AB': obj.long_cd_ab,
                'Long BA DC': obj.long_ba_dc, 'Long DC BA': obj.long_dc_ba,
                'Float AB CD': obj.float_ab_cd, 'Float CD AB': obj.float_cd_ab,
                'Float BA DC': obj.float_ba_dc, 'Float DC BA': obj.float_dc_ba,
                'Double AB CD EF GH': obj.double_ab_cd_ef_gh,
                'Double GH EF CD AB': obj.double_gh_ef_cd_ab,
                'Double BA DC FE HG': obj.double_ba_dc_fe_hg,
                'Double HG FE DC BA': obj.double_hg_fe_dc_ba, }

    def __decode(self, raw_value: List, data_format: str) -> str:
        """
        Decodes a dictionary containing binary data according to the specified data format
        and applies the given adjustments.

        :param raw_value: A list of raw values to be decoded.
        :type raw_value: List
        :param data_format: The format of the data to be decoded.
                            Valid formats are:
                            'Signed', 'Unsigned', 'Hex - ASCII', 'Binary', 'Long AB CD',
                            'Long CD AB', 'Long BA DC', 'Long DC BA', 'Float AB CD', 'Float CD AB',
                            'Float BA DC', 'Float DC BA', 'Double AB CD EF GH',
                            'Double GH EF CD AB', 'Double BA DC FE HG', 'Double HG FE DC BA'.
        :type data_format: str
        :raises ValueError: If the specified data format is not found in the format_dict.
        :raises ValueError: If the raw value is incorrect.
        :return: A string representing the decoded value with the applied adjustments.
        :rtype: str
        """
        format_dict = self.__format_dict(Decoder())
        if raw_value and all(item is not None for item in raw_value):
            if data_format in format_dict:
                return format_dict[data_format](value=raw_value)
            logger.warning(f'Error@Poller.decode_value: '
                           f'data_format {data_format} not found in format_dict.')
        logger.warning(f'Error@Poller.decode_value: raw_value {raw_value} incorrect.')

    @property
    async def poll(self) -> zip:
        header = []
        result = []
        for device in self.__devices:
            if device.active is False:
                continue
            response = await self.__get_device_data(device)
            start_pos = 0
            for registers in device.registers:
                for address, register in registers[1].items():
                    length = self.__data_len.get(register.format)
                    if not length:
                        logger.error(f'Length for {register.format} not found in data_len')
                        continue
                    data = {'raw_value': response[start_pos:length + start_pos],
                            'data_format': register.format, }
                    formatter = self.__format_dict(Decoder())
                    header.append(self.__column_namer(dev=device, reg=register))
                    value = self.__decode(**data)
                    result.append(self.__adjust(value, register.adjustments))
                    start_pos += length
        return zip(header, result)

    async def __get_device_data(self, device) -> List:
        device_data = []
        device_requests = self.__get_device_requests(device)

        client: Union[TcpClient, SerialClient] = self.__clients.get(device.connection.src)
        if client:
            if not client.connected:
                await client.connect()

        for fn, requests in device_requests.items():
            if requests:
                for request in requests:
                    response = await self.__poll(client, fn, request)
                    if response is None:
                        device_data.extend([None] * request.get('count', 0))
                    else:
                        device_data.extend(response)
        return device_data

    @staticmethod
    def __adjust(value: Any, adjustments: Dict) -> Optional[str]:
        if value is None:
            return None
        if adjustments is None:
            return value
        if isinstance(value, str):
            return value
        result: Union[str, float] = float(value)

        for adjustment in adjustments:
            for operator, operand in adjustment.items():
                if operator.isdigit() and result == int(operator):
                    return operand
                elif operator == '+':
                    result += float(operand)
                elif operator == '-':
                    result -= float(operand)
                elif operator == '*':
                    result *= float(operand)
                elif operator == '/':
                    result /= float(operand)
                elif operator == '^':
                    result **= float(operand)
        return result

    def __get_device_requests(self, device: Device) -> Dict:
        requests = {}
        for registers in device.registers:
            fn = self.__fn.get(registers[0])
            if not fn:
                logger.critical(f'Unknown modbus function {registers[0]}')
                raise ValueError(f'Unknown modbus function {registers[0]}')
            requests[fn] = []
            request = {}
            for address, register in registers[1].items():
                if register.active is False:
                    continue
                count = self.__data_len.get(register.format)
                # if `request` is  empty and not initialized:
                if not request:
                    # initialize:
                    request = {'address': int(address), 'count': count,
                               'slave': device.connection.config.address}
                else:
                    # else it has been already initialized.

                    if request['address'] + request['count'] == int(address):
                        request['count'] += count
                    else:
                        requests[fn].append(request)
                        request = {'address': int(address), 'count': count,
                                   'slave': device.connection.config.address}
            if request:
                requests[fn].append(request)
        return requests

    @asynccontextmanager
    async def __connection(self, client: Union[TcpClient, SerialClient]):
        await client.connect()
        try:
            yield client
        finally:
            client.close()

    # @staticmethod
    async def __poll(self, client: Union[TcpClient, SerialClient],
                     func: int, poll_params: Dict) -> Optional[List]:
        response = None
        try:
            match func:
                case 1:
                    response = await client.read_coils(**poll_params)
                case 2:
                    response = await client.read_discrete_inputs(**poll_params)
                case 3:
                    response = await client.read_holding_registers(**poll_params)
                case 4:
                    response = await client.read_input_registers(**poll_params)
                case _:
                    raise Exception(f'Unknown modbus function: {func}')
        except (ConnectionException, ModbusIOException) as e:
            # print(f'Variables:\n{locals()}')
            # print(f'{type(e).__name__} occurred, args={str(e.args)}\n{traceback.format_exc()}')
            logger.warning(str(e))

        if response is None or response.isError():
            return [None] * poll_params.get('count', 0)

        if func in [1, 2]:
            return list(response.bits[:poll_params.get('count', 0)])
        elif func in [3, 4]:
            return list(response.registers)
