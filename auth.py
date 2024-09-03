from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, Response, Cookie

from database import get_db
from models import UserType, Users
from schemas import UserTypeCreate
from passlib.context import CryptContext
from jose import JWTError, jwt

SECRET_KEY = "sadpkj31d13dopk1d"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 600
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_user_type(db: Session, user_type: UserTypeCreate):
    # Проверка существования типа с таким же именем
    db_user_type = db.query(UserType).filter(UserType.type_name == user_type.type_name).first()
    print(db_user_type)
    if db_user_type:
        raise HTTPException(status_code=400, detail="User Type already registered")

    # Создание нового типа
    new_user_type = UserType(
        type_name=user_type.type_name,
        description=user_type.description
    )
    db.add(new_user_type)
    db.commit()
    db.refresh(new_user_type)
    return new_user_type


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str, db: Session):
    user = db.query(Users).filter(Users.username == username).first()
    if user and verify_password(password, user.password):
        return user
    return None


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Cookie(None, alias="access_token"), db: Session = Depends(get_db)):
    print(token)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user
