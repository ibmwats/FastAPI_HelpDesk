from pydantic import BaseModel
from typing import Optional


class SAdminUserCreate(BaseModel):
    username: str
    password: str
    name: str


class SAdmin(SAdminUserCreate):
    id: int


class SUserCreate(BaseModel):
    username: str
    password: str
    name_0: str
    name_1: str
    name_2: str
    tel: Optional[str] = None
    tel_m: Optional[str] = None
    division: Optional[str] = None
    building: Optional[str] = None
    cabinet: Optional[str] = None
    last_ip: Optional[str] = None
    user_type: Optional[str] = None


class SUserTypeCreate(BaseModel):
    type_name: str
    description: str
