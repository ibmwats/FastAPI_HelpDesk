from typing import Optional

from pydantic import BaseModel


class SAdminUserCreate(BaseModel):
    username: str
    password: str
    name: str


class SAdmin(SAdminUserCreate):
    id: int

# Pydantic модель для создания пользователя
class UserCreate(BaseModel):
    username: str
    password: str
    name_0: str
    name_1: str
    name_2: str
    tel: str
    tel_m: str
    division: str
    building: str
    cabinet: str
    last_ip: str
    user_type_id: int


class UserTypeCreate(BaseModel):
    type_name: str
    description: str


