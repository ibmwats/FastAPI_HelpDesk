from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, Response, Cookie
from starlette.responses import RedirectResponse

from database import get_db
from models import User
from passlib.context import CryptContext
from jose import JWTError, jwt

SECRET_KEY = "sadpkj31d13dopk1dd1651/3*"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 600
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def hash_password(password: str) -> str:
    return pwd_context.hash(password)


async def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_user(username: str, password: str, db: AsyncSession):
    async with db as session:
        result = await session.execute(select(User).filter(User.username == username))
        user = result.scalars().first()
        if user and verify_password(password, user.password):
            return user
    return None


async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
        token: str = Cookie(None, alias="access_token"),
        db: AsyncSession = Depends(get_db)
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Redirecting to login",
            headers={"Location": "/login"}
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token 1"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Invalid token redirecting to login",
            headers={"Location": "/login"}
        )

    # Вызов асинхронной функции
    async with db as session:
        result = await session.execute(select(User).filter(User.username == username))
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user
