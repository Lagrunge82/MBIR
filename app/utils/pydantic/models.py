import uuid
from typing import Dict, Optional, List, Literal

from pydantic import BaseModel, Field, field_validator


class Register(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    active: bool
    format: str
    type: str
    adjustments: Optional[List[Dict]]


class Registers(BaseModel):
    DO: Dict[int, Register] = Field(alias='01 Read Coils')
    DI: Dict[int, Register] = Field(alias='02 Read Discrete Inputs')
    AO: Dict[int, Register] = Field(alias='03 Read Holding Registers')
    AI: Dict[int, Register] = Field(alias='04 Read Input Registers')

    @field_validator('DO', mode='before')
    def sort_do(cls, value):
        return dict(sorted(value.items()))

    @field_validator('DI', mode='before')
    def sort_di(cls, value):
        return dict(sorted(value.items()))

    @field_validator('AO', mode='before')
    def sort_ao(cls, value):
        return dict(sorted(value.items()))

    @field_validator('AI', mode='before')
    def sort_ai(cls, value):
        return dict(sorted(value.items()))


class ConnectionConfig(BaseModel):
    address: int
    timeout: int
    baudrate: int = None
    bytesize: int = None
    parity: Literal['N', 'O', 'E'] = None
    stopbits: int = None

    @field_validator('baudrate', mode='before')
    def validate_baudrate(cls, value):
        if value is not None and int(value) in [9600, 14400, 19200, 38400, 56000, 57600, 115200]:
            return value
        raise Exception(f'Invalid baudrate value: {value}')

    @field_validator('bytesize', mode='before')
    def validate_bits(cls, value):
        if value is not None and int(value) in [7, 8]:
            return value
        raise Exception(f'Invalid data bits value: {value}')

    @field_validator('stopbits', mode='before')
    def validate_stop(cls, value):
        if value is not None and int(value) in [1, 2]:
            return value
        raise Exception(f'Invalid stop bits value: {value}')


class Connection(BaseModel):
    transport: Literal['serial', 'TCP']
    src: str
    config: ConnectionConfig

    @property
    def tcp(self):
        return {'host': self.src, 'timeout': self.config.timeout / 1000}

    @property
    def serial(self):
        return {'port': self.src,
                'timeout': self.config.timeout / 1000,
                'baudrate': self.config.baudrate,
                'bytesize': self.config.bytesize,
                'parity': self.config.parity,
                'stopbits': self.config.stopbits, }


class Device(BaseModel):
    name: str
    active: bool
    connection: Connection
    registers: Registers


class Config(BaseModel):
    log_level: int = Field(alias='log level')
    table: str
    scan_rate: int = Field(alias='scan rate', default=1000)
    devices:  List[Device]
