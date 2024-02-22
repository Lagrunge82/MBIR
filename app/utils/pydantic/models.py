import uuid
from typing import Dict, Optional

from pydantic import BaseModel, Field


class Register(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    active: bool
    format: str
    type: str
    adjustments: Optional[Dict]


class Registers(BaseModel):
    DO: Dict[str, Register] = Field(alias='01 Read Coils')
    DI: Dict[str, Register] = Field(alias='02 Read Discrete Inputs')
    AO: Dict[str, Register] = Field(alias='03 Read Holding Registers')
    AI: Dict[str, Register] = Field(alias='04 Read Input Registers')


class Config(BaseModel):
    scan_rate: int = Field(alias='scan rate', default=1000)
    ip: str
    address: int = 1
    table: str
    registers: Registers
