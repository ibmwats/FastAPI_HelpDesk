import uuid

from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, Response, Cookie
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.responses import HTMLResponse
from starlette.status import HTTP_401_UNAUTHORIZED
from starlette.templating import Jinja2Templates

from auth import authenticate_user, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_current_user
from database import get_db
from models import Base, Users, UserType
from schemas import UserTypeCreate, UserCreate

# Создание приложения FastAPI
app = FastAPI()

templates = Jinja2Templates(directory="templates")


# Маршрут для отображения формы входа
@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(
        response: Response,
        username: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    user = authenticate_user(username, password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return {"message": f"Hello, {user.username}! ->> {access_token}"}


# Маршрут для выхода (logout)
@app.get("/logout")
async def logout(response: Response):
    # Удаляем cookie, в котором хранится токен
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}


@app.get("/protected")
async def protected_route(current_user: Users = Depends(get_current_user)):
    return {
        "message": f"Welcome to the protected route, {current_user.username} -> {current_user.user_type_relation.type_name}!"}
