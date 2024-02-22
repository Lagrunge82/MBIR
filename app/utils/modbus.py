"""
This module provides with class for polling devices via Modbus.

"""

from __future__ import annotations

__author__ = "Ilya Molodkin"
__date__ = "2023-04-22"
__version__ = "1.0"
__license__ = "MIT License"

import traceback
from datetime import datetime
from typing import Optional, Dict, List, Any, Union

# import memory_profiler
# from guppy import hpy

import pymodbus
from pymodbus import client as modbus
from pymodbus.pdu import ModbusResponse
from pymodbus.exceptions import ModbusException

from app.utils.utils import isNumerical
from app.utils.coders import Encoder, Decoder
from app.utils.pydantic.models import Config
from app.utils.enums import FN


class Poller:
    """
    A class for polling data from a Modbus device.

    :param config: A dictionary of config for the Modbus connection.
    :type config: Dict

    :ivar reg_len: A dictionary of register lengths for various data types.
    :type reg_len: Dict
    :ivar _modbus: A modbus instance for the Modbus connection.
    :type _modbus: modbus
    :ivar _config: A dictionary of config for the Modbus connection.
    :type _config: Dict
    :ivar _connection: The Modbus connection object.
    :type _connection: Optional[Union[self._modbus.ModbusTcpClient, 
                                      self._modbus.ModbusSerialClient]]
    :ivar _requests: A dictionary of requests sent to the Modbus device.
    :type _requests: Dict 
    :ivar _decoder: A Decoder instance.
    :type _decoder: Decoder 

    :return: An instance of the Poller class.
    """
    _modbus = None

    def __init__(self, config: Config) -> None:
        self.reg_len: Dict = {'Signed': 1, 'Unsigned': 1,
                              'Hex - ASCII': 1, 'Binary': 1,
                              'Long AB CD': 2, 'Long CD AB': 2,
                              'Long BA DC': 2, 'Long DC BA': 2,
                              'Float AB CD': 2, 'Float CD AB': 2,
                              'Float BA DC': 2, 'Float DC BA': 2,
                              'Double AB CD EF GH': 4, 'Double GH EF CD AB': 4,
                              'Double BA DC FE HG': 4, 'Double HG FE DC BA': 4, }
        self._modbus: modbus = modbus
        self._config: Config = config
        self._connection: Optional[Union[Poller._modbus.ModbusTcpClient,
                                         Poller._modbus.ModbusSerialClient]] = None
        self._requests: Dict = {}
        self._decoder: Decoder = Decoder()
        self._encoder: Encoder = Encoder()

    @property
    def scan_rate(self) -> Optional[int]:
        """
        Get the scan rate setting for the device.

        :return: An integer representing the scan rate setting for the device, 
                 or None if the setting is not available.
        :rtype: Optional[int]
        """
        return self._config.scan_rate
    
    @scan_rate.setter
    def scan_rate(self, value: int) -> None:
        """
        Sets the scan rate value for the poller.

        :param value: An integer representing the scan rate value to set.
        :type value: int
        :return: nothing
        :rtype: None
        """
        self._config.scan_rate = value

    @property
    def registers(self) -> Optional[List]:
        """
        Get the current values of all requested Modbus registers.

        :return: A list of register values, or None if an error occurred.
        :rtype: Optional[List]

        """
        result: Optional[List] = []
        try:
            # Iterate over each Modbus request in the poller's requests dictionary
            for fn, requests in self.__requests.items():
                for request in requests.values():
                    # Build a parameters dictionary for the Modbus request
                    params: Dict = {'func': fn,
                                    'reg_address': int(request['address']),
                                    'reg_qty': int(request['quantity'])}

                    # Call the Modbus poll method with the parameters and get the response
                    response = self._poll(**params)

                    # Process each mapped register in the request
                    # and append its value to the result list
                    for pos, register in request['map'].items():
                        content = register['content']
                        length = int(self.reg_len[content.format])
                        raw_value: List = response[pos:pos+length] if response else []
                        value = self.decode_value(raw_value=raw_value,
                                                  data_format=content.format,
                                                  adjustments=content.adjustments or [])
                        result.append({'address': register['address'],
                                       'name': content.name,
                                       'format': content.format,
                                       'value': value,
                                       'timestamp': datetime.now().strftime('%d-%m-%Y %H:%M:%S')})
            # Return the result list
            del response
            del content
            return result
        except ModbusException as e:
            # Handle exceptions by printing error information and returning None
            print(f'Error: registers@modbus.py, result: {result}, type: {type(result)}')
            print(f'{type(e).__name__} occurred, args={str(e.args)}\n{traceback.format_exc()}')
        finally:
            pass
        # If an error occurred, return None
        return None

    @property
    def __requests(self) -> Dict:
        result: Dict = {}
        for fn, registers in dict(self._config.registers).items():
            requests: Dict = {}
            for address, register in registers.items():
                index = len(requests) - 1
                if index == -1:
                    requests[0] = {
                        'address': address,
                        'quantity': self.reg_len[register.format],
                        'map': {
                            0: {
                                'address': address,
                                'length': self.reg_len[register.format],
                                'content': register
                            }
                        }
                    }
                elif index > -1:
                    # Мап - список параметров регистров для конкретной группы регистров,
                    # создан для упрощения сопоставления полученного списка значений с регистрами,
                    # к которым эти значения относятся.
                    # Индекс последнего регистра в мапе
                    prev_map_index = max(requests[index]['map'].keys())

                    # данные последнего регистра в мапе
                    prev_map_data = requests[index]['map'][prev_map_index]

                    # Адрес последнего регистра
                    prev_data_addr = prev_map_data['address']

                    # длина последнего регистра
                    prev_data_len = prev_map_data['length']

                    # Если у нашего регистра адрес не равен адресу предыдущего + сдвиг по длине,
                    # то этот регистр - первый регистр следующей группы регистров
                    if int(address) != int(prev_data_addr) + int(prev_data_len):
                        requests[index + 1] = {
                            'address': address,
                            'quantity': self.reg_len[register.format],
                            'map': {
                                0: {
                                    'address': address,
                                    'length': self.reg_len[register.format],
                                    'content': register
                                }
                            }
                        }
                    # Иначе это регистры из одной группы
                    elif int(address) == int(prev_data_addr) + int(prev_data_len):
                        request: Dict = requests[index]
                        request['quantity'] += self.reg_len[register.format]
                        map_index: int = prev_map_index + prev_data_len
                        request['map'][map_index] = {'address': address,
                                                     'length': self.reg_len[register.format],
                                                     'content': register}

                else:
                    raise Exception(f'Invalid index {index}')
            func_id = FN[fn].value
            result[func_id] = requests
        return result

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

    def decode_value(self, raw_value: List, data_format: str, adjustments: List) -> str:
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
        :param adjustments: A list of adjustments to be applied to the decoded value.
        :type adjustments: List
        :raises ValueError: If the specified data format is not found in the format_dict.
        :raises ValueError: If the raw value is incorrect.
        :return: A string representing the decoded value with the applied adjustments.
        :rtype: str
        """
        format_dict: Dict = self.__format_dict(self._decoder)
        if raw_value:
            if data_format in format_dict:
                return self._adjust(format_dict[data_format](value=raw_value), adjustments)
            raise ValueError('Error@Poller.decode_value.',
                             f'data_format {data_format} not found in format_dict.')
        raise ValueError('Error@Poller.decode_value.',
                         f'raw_value {raw_value} incorrect.')
    
    def encode_value(self, value: Union[str, float], 
                     data_format: str, 
                     adjustments: List) -> List[int]:
        """
        Encodes a value according to a specified data format, applying any necessary adjustments.

        :param value: The value to encode, as a string or float.
        :type value: Union[str, float]
        :param data_format: The format to encode the value in.
        :type data_format: str
        :param adjustments:  A list of dictionaries representing adjustments to apply to the value.
        :type adjustments: List
        :raises ValueError: If the specified data_format is not supported.
        :return: The encoded value as a list of pymodbus registers.
        :rtype: List[int]
        """
        format_dict: Dict = self.__format_dict(self._encoder)
        if data_format in format_dict:
            if data_format not in ['Hex - ASCII', 'Binary']:
                if isNumerical(value=value):
                    value = self._adjust_reverse(value=float(value), adjustments=adjustments)
                else:
                    return None
            return format_dict[data_format](value=value)
        raise ValueError('Error@Poller.encode_value.',
                         f'data_format {data_format} not found in format_dict.')
        
    @staticmethod
    def _adjust(value: Any, adjustments: Dict) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        result: Union[str, float] = float(value)

        for adjustment in adjustments:
            for operator, operand in adjustment.items():
                if operator.isdigit():
                    if result == int(operator):
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
        return str(f"{result:.2f}")
    
    @staticmethod
    def _adjust_reverse(value: float, adjustments: Dict) -> float:
        for adjustment in adjustments[::-1]:
            for operator, operand in adjustment.items():
                if operator == '+':
                    value -= float(operand)
                elif operator == '-':
                    value += float(operand)
                elif operator == '*':
                    value /= float(operand)
                elif operator == '/':
                    value *= float(operand)
                elif operator == '^':
                    value **= (1 / float(operand))
        return value

    def _get_connection(self) -> Union[Poller._modbus.ModbusTcpClient]:
        # protocol: str = self._get('protocol')
        protocol: str = 'TCP'
        if protocol == 'TCP':
            ip: str = self._config.ip
            if ip:
                return self._modbus.ModbusTcpClient(ip)
            print('Exception@_get_connection (TCP)')
        print('Exception@_get_connection')

    def connect(self) -> None:
        """
        Connects the instance to a Modbus device.

        :return: nothing
        :rtype: None
        """
        self._connection: Poller._modbus.ModbusTcpClient = self._get_connection()
        self._connection.connect()
        print(f'{self} successfully connected to {self._connection}.')

    @property
    def is_connected(self) -> bool:
        """
        Returns a boolean indicating whether the instance is currently connected to a server.

        :return: True if the instance is connected to a Modbus device, False otherwise.
        :rtype: bool
        """
        return self._connection.is_socket_open()

    def _poll(self, func: int, reg_address: int, reg_qty: int) -> Optional[List]:
        slave_id: int = self._config.address
        poll_params: Dict = {'address': reg_address,
                             'count': reg_qty,
                             'slave': slave_id}
        response: Optional[ModbusResponse] = None
        result: Optional[list] = None
        try:
            if func == 1:
                response = self._connection.read_coils(**poll_params)
            elif func == 2:
                response = self._connection.read_discrete_inputs(**poll_params)
            elif func == 3:
                response = self._connection.read_holding_registers(**poll_params)
            elif func == 4:
                response = self._connection.read_input_registers(**poll_params)
            else:
                print('Exception')
        except pymodbus.exceptions.ConnectionException as e:  # pylint: disable=unused-variable
            print(f'Error: poll@modbus.py, result: {result}, type: {type(result)}')
            # print(f'{type(e).__name__} occurred, args={str(e.args)}\n{traceback.format_exc()}')
            return None

        if response is not None:
            if not response.isError():
                if func in [1, 2]:
                    result = list(response.bits[:reg_qty])
                if func in [3, 4]:
                    result = list(response.registers)
                del response
                return result
        return None
    
    def writeSingleCoil(self, address: int, value: bool) -> ModbusResponse:
        """
        Write a single coil value to the specified address in the Modbus device.

        :param address: The address to write the coil value to.
        :type address: int
        :param value: The value to be written to the Modbus device (True for 1, False for 0).
        :type value: bool
        :return: A ModbusResponse object containing the status of the write operation.
        :rtype: ModbusResponse
        """
        slave_id: int = self._config.address
        return self._connection.write_coil(address=int(address), 
                                           value=value, 
                                           slave=slave_id)
    
    def writeRegisters(self, address: int, value: List) -> ModbusResponse:
        """
        Write a list of values to holding registers with the specified address 
        in the Modbus device.

        :param address: The address to write the values to.
        :type address: int
        :param value: A list of values to be written to the Modbus device.
        :type value: List
        :return: A ModbusResponse object containing the status of the write operation.
        :rtype: ModbusResponse
        """
        slave_id: int = self._config.address
        return self._connection.write_registers(address=int(address),
                                                values=value, 
                                                slave=slave_id)

    def disconnect(self) -> None:
        """
        Close connection to device and print status
        
        """
        if self._connection:
            self._connection.close()
            print(f'{self} successfully disconnected from {self._connection}.')
        else:
            print(f'{self} already disconnected from {self._connection}.')
