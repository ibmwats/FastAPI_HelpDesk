import uuid

from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, Response, Cookie
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.status import HTTP_401_UNAUTHORIZED
from starlette.templating import Jinja2Templates

import routers.admin
from auth import authenticate_user, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_current_user, hash_password
from database import get_db
from models import Base, Users, UserType
from schemas import UserTypeCreate, UserCreate

# Создание приложения FastAPI
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(routers.admin.router, prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")


# Маршрут для отображения формы входа
@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(
        request: Request,
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

    # Устанавливаем токен в cookie
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    #  Обновление IP адреса пользователя
    client_ip = request.client.host
    user.last_ip = client_ip
    user.last_entry = func.now()
    db.commit()

    #  Проверяем, является ли пользователь администратором
    if 'admin' in user.user_type_relation.type_name:
        rr = RedirectResponse('/admin/', status_code=303)
        rr.set_cookie(key="access_token", value=access_token, httponly=True)
        return rr
    else:
        return {"message": f"Hello, {user.username}! ->> {access_token}"}


# Маршрут для выхода (logout)
@app.get("/logout")
async def logout(response: Response):
    # Удаляем cookie, в котором хранится токен
    response.delete_cookie(key="access_token")
    # return {"message": "Successfully logged out"}
    return RedirectResponse('/login', status_code=303)


@app.get("/protected")
async def protected_route(current_user: Users = Depends(get_current_user)):
    return {
        "message": f"Welcome to the protected route, {current_user.username} -> {current_user.user_type_relation.type_name}!"}


@app.get("/forgot-your-password")
async def forgot_password(request: Request):
    client_ip = request.client.host
    print(client_ip)
    return templates.TemplateResponse("восстановление_пароля.html", {"request": request})


@app.post("/forgot-your-password")
async def forgot_password_view(request: Request, username: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    print('Делаем расшифровку пароля')
    print(user.password)
    my_pass = '123'
    return templates.TemplateResponse("восстановление_пароля.html", {"request": request, "my_pass": my_pass})


@app.get("/registration")
async def registration(request: Request):
    client_ip = request.client.host
    print(client_ip)
    return templates.TemplateResponse("регистрация.html", {"request": request})


@app.post("/registration")
async def registration_post(request: Request,
                            username: str = Form(...),
                            password: str = Form(...),
                            name_0: str = Form(...),
                            name_1: str = Form(...),
                            name_2: str = Form(...),
                            tel: str = Form(...),
                            tel_m: str = Form(...),
                            division: str = Form(...),
                            building: str = Form(...),
                            cabinet: str = Form(...),
                            db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        pass_hash = hash_password(password)
        user_type_id = 3  # 3 - users, назначаем по умолчаюнию
        last_ip = request.client.host

        new_user = Users(username=username,
                         password=pass_hash,
                         name_0=name_0,
                         name_1=name_1,
                         name_2=name_2,
                         tel=tel,
                         tel_m=tel_m,
                         division=division,
                         building=building,
                         cabinet=cabinet,
                         last_entry=func.now(),
                         last_ip=last_ip,
                         user_type_id=user_type_id)
        db.add(new_user)
        db.commit()
        message = "<strong>Поздравляем!</strong> Вы успешно зарегистрировались! Войдите в систему под своим именем пользователя и паролем"
        #  return RedirectResponse(url=f"/create_user?created_user_id={new_user.id}", status_code=303)
        return templates.TemplateResponse("login.html", {"request": request, "message": message})
    else:
        message = "<strong>Имя пользователя</strong> уже используется!"
        return templates.TemplateResponse("регистрация.html", {"request": request, "message": message})
