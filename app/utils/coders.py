"""
Module provides with classes decoding and encoding pymodbus registers data.

"""

__author__ = "Ilya Molodkin"
__date__ = "2023-04-22"
__version__ = "1.0"
__license__ = "MIT License"


from typing import Dict, List
import re

from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder


class Decoder:
    """
    Decodes binary data using various formats.
    
    """
    @staticmethod
    def signed(value: List) -> int:
        """
        Decodes signed integer from the given list value.

        :param value: A list containing binary data to decode.
        :type value: List
        :return: Decoded data in signed integer format.
        :rtype: int
        """
        return int(value[0]) - 65536 if int(value[0]) > 32767 else int(value[0])

    @staticmethod
    def unsigned(value: List) -> int:
        """
        Decodes unsigned integer from the given list value.

        :param value: A list containing binary data to decode.
        :type value: List
        :return: Decoded data in unsigned integer format.
        :rtype: int
        """
        return int(value[0])

    @staticmethod
    def hex_ascii(value: List) -> str:
        """
        Decodes hexadecimal ASCII string from the given list value.

        :param value: A list containing binary data to decode.
        :type value: List
        :return: Decoded data in hexadecimal ASCII format.
        :rtype: str
        """
        return hex(int(value[0]))

    @staticmethod
    def binary(value: List) -> str:
        """
        Decodes binary string from the given list value.

        :param value: A list containing binary data to decode.
        :type value: List
        :return: Decoded data in binary format.
        :rtype: str
        """
        return ' '.join([format(value[0], '016b')[4*x:4*(x+1)] for x in range(4)])

    @staticmethod
    def long_ab_cd(value: List) -> int:
        """
        Decodes 32-bit integer from the given list value in the format AB-CD
        (big-endian).

        :param value: A list containing binary data to decode.
        :type value: List
        :return: Decoded data in 32-bit integer format.
        :rtype: int
        """
        data = {'registers': value, 'byteorder': Endian.BIG, 'wordorder': Endian.BIG}
        return BinaryPayloadDecoder.fromRegisters(**data).decode_32bit_int()

    @staticmethod
    def long_cd_ab(value: List) -> int:
        """
        Decodes 32-bit integer from the given list value in the format CD-AB
        (little-endian).

        :param value: A list containing binary data to decode.
        :type value: List
        :return: Decoded data in 32-bit integer format.
        :rtype: int
        """
        data = {'registers': value, 'byteorder': Endian.BIG, 'wordorder': Endian.LITTLE}
        return BinaryPayloadDecoder.fromRegisters(**data).decode_32bit_int()

    @staticmethod
    def long_ba_dc(value: List) -> int:
        """
        Decodes 32-bit integer from the given list value in the format BA-DC
        (little-endian, swapped bytes).

        :param value: A list containing binary data to decode.
        :type value: List
        :return: Decoded data in 32-bit integer format.
        :rtype: int
        """
        data = {'registers': value, 'byteorder': Endian.LITTLE, 'wordorder': Endian.BIG}
        return BinaryPayloadDecoder.fromRegisters(**data).decode_32bit_int()

    @staticmethod
    def long_dc_ba(value: List) -> int:
        """
        Decodes 32-bit integer from the given list value in the format DC-BA
        (little-endian, swapped words).

        :param value: A list containing binary data to decode.
        :type value: List
        :return: Decoded data in 32-bit integer format.
        :rtype: int
        """
        data = {'registers': value, 'byteorder': Endian.LITTLE, 'wordorder': Endian.LITTLE}
        return BinaryPayloadDecoder.fromRegisters(**data).decode_32bit_int()

    @staticmethod
    def float_ab_cd(value: List) -> float:
        """
        Decodes 32-bit float from the given list value in the format AB-CD
        (big-endian).

        :param value: A list containing binary data to decode.
        :type value: List
        :return: Decoded data in 32-bit float format.
        :rtype: float
        """
        data = {'registers': value, 'byteorder': Endian.BIG, 'wordorder': Endian.BIG}
        return BinaryPayloadDecoder.fromRegisters(**data).decode_32bit_float()

    @staticmethod
    def float_cd_ab(value: List) -> float:
        """
        Decodes 32-bit float from the given list value in the format CD-AB
        (little-endian).

        :param value: A list containing binary data to decode.
        :type value: List
        :return: Decoded data in 32-bit float format.
        :rtype: float
        """
        data = {'registers': value, 'byteorder': Endian.BIG, 'wordorder': Endian.LITTLE}
        return BinaryPayloadDecoder.fromRegisters(**data).decode_32bit_float()

    @staticmethod
    def float_ba_dc(value: List) -> float:
        """
        Decodes 32-bit float from the given list value in the format BA-DC
        (little-endian, swapped bytes).

        :param value: A list containing binary data to decode.
        :type value: List
        :return: Decoded data in 32-bit float format.
        :rtype: float
        """
        data = {'registers': value, 'byteorder': Endian.LITTLE, 'wordorder': Endian.BIG}
        return BinaryPayloadDecoder.fromRegisters(**data).decode_32bit_float()

    @staticmethod
    def float_dc_ba(value: List) -> float:
        """
        Decodes 32-bit float from the given list value in the format DC-BA
        (little-endian, swapped words).

        :param value: A list containing binary data to decode.
        :type value: List
        :return: Decoded data in 32-bit float format.
        :rtype: float
        """
        data = {'registers': value, 'byteorder': Endian.LITTLE, 'wordorder': Endian.LITTLE}
        return BinaryPayloadDecoder.fromRegisters(**data).decode_32bit_float()

    @staticmethod
    def double_ab_cd_ef_gh(value: List) -> float:
        """
        Decodes 64-bit float from the given list value in the format AB-CD-EF-GH
        (big-endian).

        :param value: A list containing binary data to decode.
        :type value: List
        :return: Decoded data in 64-bit float format.
        :rtype: float
        """
        data = {'registers': value, 'byteorder': Endian.BIG, 'wordorder': Endian.BIG}
        return BinaryPayloadDecoder.fromRegisters(**data).decode_64bit_float()

    @staticmethod
    def double_gh_ef_cd_ab(value: List) -> float:
        """
        Decodes 64-bit float from the given list value in the format GH-EF-CD-AB
        (big-endian, swapped bytes).

        :param value: A list containing binary data to decode.
        :type value: List
        :return: Decoded data in 64-bit float format.
        :rtype: float
        """
        data = {'registers': value, 'byteorder': Endian.BIG, 'wordorder': Endian.LITTLE}
        return BinaryPayloadDecoder.fromRegisters(**data).decode_64bit_float()

    @staticmethod
    def double_ba_dc_fe_hg(value: List) -> float:
        """
        Decodes 64-bit float from the given list value in the format BA-DC-FE-HG
        (little-endian, swapped words).

        :param value: A list containing binary data to decode.
        :type value: List
        :return: Decoded data in 64-bit float format.
        :rtype: float
        """
        data = {'registers': value, 'byteorder': Endian.LITTLE, 'wordorder': Endian.BIG}
        return BinaryPayloadDecoder.fromRegisters(**data).decode_64bit_float()

    @staticmethod
    def double_hg_fe_dc_ba(value: List) -> float:
        """
        Decodes 64-bit float from the given list value in the format HG-FE-DC-BA
        (little-endian, swapped words).

        :param value: A list containing binary data to decode.
        :type value: List
        :return: Decoded data in 64-bit float format.
        :rtype: float
        """
        data = {'registers': value, 'byteorder': Endian.LITTLE, 'wordorder': Endian.LITTLE}
        return BinaryPayloadDecoder.fromRegisters(**data).decode_64bit_float()

class Encoder:
    """
    A class for encoding various numerical data types as a list of pymodbus registers.

    .. note::
        This class uses the `pymodbus` library to build the register list 
        for the given numerical value.
    """
    def __init__(self) -> None:
        self._hex_ascii_pattern = re.compile(r'^0x[0-9a-fA-F]{1,4}$')
        self._binary_pattern = re.compile(r'^[01]{4} [01]{4} [01]{4} [01]{4}$')

    def _16bit_int(self, value: str, data_format: Dict) -> List[int]:
        builder = BinaryPayloadBuilder(**data_format)
        builder.add_16bit_int(int(value))
        return builder.to_registers()

    def _16bit_uint(self, value: str, data_format: Dict) -> List[int]:
        builder = BinaryPayloadBuilder(**data_format)
        builder.add_16bit_uint(int(value))
        return builder.to_registers()

    def _32bit_int(self, value: str, data_format: Dict) -> List[int]:
        builder = BinaryPayloadBuilder(**data_format)
        builder.add_32bit_int(int(value))
        return builder.to_registers()

    def _32bit_float(self, value: str, data_format: Dict) -> List[int]:
        builder = BinaryPayloadBuilder(**data_format)
        builder.add_32bit_float(float(value))
        return builder.to_registers()

    def _64bit_float(self, value: str, data_format: Dict) -> List[int]:
        builder = BinaryPayloadBuilder(**data_format)
        builder.add_64bit_float(float(value))
        return builder.to_registers()

    def signed(self, value: str) -> List[int]:
        """
        Encodes 16-bit signed integer value as a list of registers.

        :param value: 16-bit signed integer value.
        :type value: str
        :return: list of registers.
        :rtype: List[int]
        """
        if -32768 <= value <= 32767:
            data_format: Dict = {'byteorder': Endian.Big, }
            return self._16bit_int(value=value, data_format=data_format)
        return None

    def unsigned(self, value: str) -> List[int]:
        """
        Encodes 16-bit signed unsigned value as a list of registers.

        :param value: 16-bit signed unsigned value.
        :type value: str
        :return: list of registers.
        :rtype: List[int]
        """
        if 0 <= value <= 65535:
            data_format: Dict = {'byteorder': Endian.Big, }
            return self._16bit_uint(value=value, data_format=data_format)
        return None

    def hex_ascii(self, value: str) -> List[int]:
        """
        Encodes hexadecimal ASCII string as a list of registers.

        :param value: hexadecimal ASCII string.
        :type value: str
        :return: list of registers.
        :rtype: List[int]
        """
        if self._hex_ascii_pattern.match(value):
            data_format: Dict = {'byteorder': Endian.Big, }
            return self._16bit_uint(value=int(value, 16), data_format=data_format)
        return None

    def binary(self, value: str) -> List[int]:
        """
        Encodes binary string as a list of registers.

        :param value: binary string.
        :type value: str
        :return: list of registers.
        :rtype: List[int]
        """
        if self._binary_pattern.match(value):
            data_format: Dict = {'byteorder': Endian.Big, }
            return self._16bit_uint(value=int(value.replace(' ', ''), 2), data_format=data_format)
        return None

    def long_ab_cd(self, value: str) -> List[int]:
        """
        Encodes 32-bit integer as a list of registers in the format AB-CD
        (big-endian).

        :param value: 32-bit integer.
        :type value: str
        :return: list of registers.
        :rtype: List[int]
        """
        data_format: Dict = {'byteorder': Endian.Big,
                             'wordorder': Endian.Big, }
        return self._32bit_int(value=value, data_format=data_format)

    def long_cd_ab(self, value: str) -> List[int]:
        """
        Encodes 32-bit integer as a list of registers in the format CD-AB
        (little-endian).

        :param value: 32-bit integer.
        :type value: str
        :return: list of registers.
        :rtype: List[int]
        """
        data_format: Dict = {'byteorder': Endian.Big,
                             'wordorder': Endian.Little, }
        return self._32bit_int(value=value, data_format=data_format)

    def long_ba_dc(self, value: str) -> List[int]:
        """
        Encodes 32-bit integer as a list of registers in the format BA-DC
        (little-endian, swapped bytes).

        :param value: 32-bit integer.
        :type value: str
        :return: list of registers.
        :rtype: List[int]
        """
        data_format: Dict = {'byteorder': Endian.Little,
                             'wordorder': Endian.Big, }
        return self._32bit_int(value=value, data_format=data_format)

    def long_dc_ba(self, value: str) -> List[int]:
        """
        Encodes 32-bit integer as a list of registers in the format DC-BA
        (little-endian, swapped words).

        :param value: 32-bit integer.
        :type value: str
        :return: list of registers.
        :rtype: List[int]
        """
        data_format: Dict = {'byteorder': Endian.Little,
                             'wordorder': Endian.Little, }
        return self._32bit_int(value=value, data_format=data_format)

    def float_ab_cd(self, value: str) -> List[int]:
        """
        Encodes 32-bit float as a list of registers in the format AB-CD
        (big-endian).

        :param value: 32-bit float.
        :type value: str
        :return: list of registers.
        :rtype: List[int]
        """
        data_format: Dict = {'byteorder': Endian.Big,
                             'wordorder': Endian.Big, }
        return self._32bit_float(value=value, data_format=data_format)

    def float_cd_ab(self, value: str) -> List[int]:
        """
        Encodes 32-bit float as a list of registers in the format CD-AB
        (little-endian).

        :param value: 32-bit float.
        :type value: str
        :return: list of registers.
        :rtype: List[int]
        """
        data_format: Dict = {'byteorder': Endian.Big,
                             'wordorder': Endian.Little, }
        return self._32bit_float(value=value, data_format=data_format)

    def float_ba_dc(self, value: str) -> List[int]:
        """
        Encodes 32-bit float as a list of registers in the format BA-DC
        (little-endian, swapped bytes).

        :param value: 32-bit float.
        :type value: str
        :return: list of registers.
        :rtype: List[int]
        """
        data_format: Dict = {'byteorder': Endian.Little,
                             'wordorder': Endian.Big, }
        return self._32bit_float(value=value, data_format=data_format)

    def float_dc_ba(self, value: str) -> List[int]:
        """
        Encodes 32-bit float as a list of registers in the format DC-BA
        (little-endian, swapped words).

        :param value: 32-bit float.
        :type value: str
        :return: list of registers.
        :rtype: List[int]
        """
        data_format: Dict = {'byteorder': Endian.Little,
                             'wordorder': Endian.Little, }
        return self._32bit_float(value=value, data_format=data_format)

    def double_ab_cd_ef_gh(self, value: str) -> List[int]:
        """
        Encodes 64-bit float as a list of registers in the format AB-CD-EF-GH
        (big-endian).

        :param value: 64-bit float.
        :type value: str
        :return: list of registers.
        :rtype: List[int]
        """
        data_format: Dict = {'byteorder': Endian.Big,
                             'wordorder': Endian.Big, }
        return self._64bit_float(value=value, data_format=data_format)

    def double_gh_ef_cd_ab(self, value: str) -> List[int]:
        """
        Encodes 64-bit float as a list of registers in the format GH-EF-CD-AB
        (big-endian, swapped bytes).

        :param value: 64-bit float.
        :type value: str
        :return: list of registers.
        :rtype: List[int]
        """
        data_format: Dict = {'byteorder': Endian.Big,
                             'wordorder': Endian.Little, }
        return self._64bit_float(value=value, data_format=data_format)

    def double_ba_dc_fe_hg(self, value: str) -> List[int]:
        """
        Encodes 64-bit float as a list of registers in the format BA-DC-FE-HG
        (little-endian, swapped words).

        :param value: 64-bit float.
        :type value: str
        :return: list of registers.
        :rtype: List[int]
        """
        data_format: Dict = {'byteorder': Endian.Little,
                             'wordorder': Endian.Big, }
        return self._64bit_float(value=value, data_format=data_format)

    def double_hg_fe_dc_ba(self, value: str) -> List[int]:
        """
        Encodes 64-bit float as a list of registers in the format HG-FE-DC-BA
        (little-endian, swapped words).

        :param value: 64-bit float.
        :type value: str
        :return: list of registers.
        :rtype: List[int]
        """
        data_format: Dict = {'byteorder': Endian.Little,
                             'wordorder': Endian.Little, }
        return self._64bit_float(value=value, data_format=data_format)
