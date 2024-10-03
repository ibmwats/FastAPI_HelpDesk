import uuid

from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, Response, Cookie
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.status import HTTP_401_UNAUTHORIZED
from starlette.templating import Jinja2Templates

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

import routers.admin
import routers.user
from auth import authenticate_user, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_current_user, hash_password
from database import init_models, get_db
from models import Base, User, Otdel
import configparser  # settings.ini

from routers.func import fetch_otdels

# Создание приложения FastAPI
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(routers.admin.router, prefix="/admin", tags=["admin"])
app.include_router(routers.user.router, prefix="/user", tags=["user"])
templates = Jinja2Templates(directory="templates")

# settings.ini
config = configparser.ConfigParser()
config.read('settings.ini')
roles = config.get('settings', 'roles').split(',')


@app.on_event("startup")
async def on_startup():
    # Инициализация базы данных при старте приложения
    await init_models()


async def redirect(user, access_token):
    if user.dostup == 'пользователь':
        rr = RedirectResponse('/user/', status_code=303)
    elif user.dostup == 'админ' or user.dostup == 'супер_админ':
        rr = RedirectResponse('/admin/', status_code=303)
    else:
        return {"Ошибка": "Ошибка авторизации!"}
    # Устанавливаем токен в cookie
    rr.set_cookie(key="access_token", value=access_token, httponly=True)

    return rr


# Маршрут для отображения формы входа
@app.get("/")
@app.get("/login")
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(
        request: Request,
        response: Response,
        username: str = Form(...),
        password: str = Form(...),
        db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(username, password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Устанавливаем токен в cookie
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    #  Обновление IP адреса пользователя

    # Перенаправление и установка токена
    return await redirect(user, access_token)


# Маршрут для выхода (logout)
@app.get("/logout")
async def logout(request: Request, response: Response):
    '''
    cookies = request.cookies

    # Удаляем каждую cookie, явно указывая путь и домен (если нужно)
    for cookie in cookies:
        response.delete_cookie(cookie, path="/", httponly=True)
    '''
    message = 'Вы успешно вышли из системы!'
    response = templates.TemplateResponse("login.html", {"request": request, "message": message})
    response.delete_cookie("access_token")
    return response


@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {
        "message": f"Welcome to the protected route, {current_user.username} -> {current_user.dostup}!"}


@app.get("/forgot-your-password")
async def forgot_password(request: Request):
    client_ip = request.client.host
    print(client_ip)
    return templates.TemplateResponse("восстановление_пароля.html", {"request": request})


@app.get("/registration", response_class=HTMLResponse)
async def registration(request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host
    print(f"Client IP: {client_ip}")

    try:
        otdels = await fetch_otdels(db)
        # Передача данных в шаблон
        return templates.TemplateResponse("регистрация.html", {"request": request, "otdels": otdels})

    except SQLAlchemyError as e:
        return {f"Ошибка базы данных: {e}"}


@app.post("/registration")
async def registration_post(request: Request,
                            username: str = Form(...),
                            password: str = Form(...),
                            surname: str = Form(...),
                            name: str = Form(...),
                            patronymic: str = Form(...),
                            tel_stationary: str = Form(...),
                            tel_mobile: str = Form(...),
                            otdel_id: int = Form(default=None),
                            building: str = Form(...),
                            cabinet: str = Form(...),
                            db: AsyncSession = Depends(get_db)):
    try:
        # Проверка, существует ли пользователь с таким именем
        result = await db.execute(select(User).filter(User.username == username))
        user = result.scalar_one_or_none()

        if not user:
            pass_hash = await hash_password(password)
            last_ip = request.client.host

            new_user = User(
                username=username,
                password=pass_hash,
                surname=surname,
                name=name,
                patronymic=patronymic,
                tel_stationary=tel_stationary,
                tel_mobile=tel_mobile,
                otdel_id=otdel_id,
                building=building,
                cabinet=cabinet,
                last_ip=last_ip
            )

            # Добавление нового пользователя в базу данных
            db.add(new_user)
            await db.commit()

            message = "<strong>Поздравляем!</strong> Вы успешно зарегистрировались! Войдите в систему под своим именем пользователя и паролем."
            return templates.TemplateResponse("login.html", {"request": request, "message": message})
        else:
            # Пользователь с таким именем уже существует
            message = "<strong>Имя пользователя</strong> уже используется!"
            return templates.TemplateResponse("регистрация.html", {"request": request, "message": message})

    except SQLAlchemyError:
        await db.rollback()  # Откатить транзакцию в случае ошибки
        return {"ОШИБКА": "Произошла ошибка в базе данных"}

    except Exception as e:
        return {"ОШИБКА": f"Произошла неизвестная ошибка: {str(e)}"}
