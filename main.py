from fastapi import FastAPI, Request, Depends, HTTPException, Form, APIRouter, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, HTMLResponse

from crud import get_admin_users
from database import engine, SessionLocal, Base, get_db
from models import Users, Tasks, StatusTask, File, Categories
from routers import admin
from routers.auth import get_current_user, authenticate_user, create_access_token, get_admin_user
from schemas import SAdminUserCreate, SUserCreate, SAdmin

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

#  pip install python-jose
#  pip install passlib
#  fastapi dev main.py

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

# Подключаем маршруты админ-панели
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


@app.post("/admin_create")
async def create_admin(
        username: str = Form(...),
        password: str = Form(...),
        name: str = Form(...),
        db: Session = Depends(get_db)
):
    db_user = Users(username=username, password=password, name=name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return RedirectResponse(url="/", status_code=303)


@app.post("/users/")
async def create_user(user: SUserCreate, db: Session = Depends(get_db)):
    db_user = Users(
        username=user.username,
        password=user.password,
        name_0=user.name_0,
        name_1=user.name_1,
        name_2=user.name_2,
        tel=user.tel,
        tel_m=user.tel_m,
        division=user.division,
        building=user.building,
        cabinet=user.cabinet,
        last_ip=user.last_ip,
        user_type=user.user_type
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


#  Логика авторизации
#  Маршрут для получения токена
@app.post("/token", response_class=HTMLResponse)
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Incorrect username or password"})

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(data={"sub": user.username, "user_type": user.user_type_relation.type_name},
                                       expires_delta=access_token_expires)
    response = RedirectResponse(url="/protected-route", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="Authorization", value=f"Bearer {access_token}", httponly=True)
    print(f'Пользователь имеет привелегии: {user.username}')
    return response


# Маршрут для отображения страницы входа
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# Пример защищенного маршрута
@app.get("/protected-route", response_class=HTMLResponse)
async def read_protected_route(request: Request, current_user: Users = Depends(get_current_user)):
    return templates.TemplateResponse("protected_route.html", {"request": request, "username": current_user.username})


# Пример маршрута для администраторов
@app.get("/admin-only", response_class=HTMLResponse)
async def admin_only_route(request: Request, current_user: Users = Depends(get_admin_user)):
    return templates.TemplateResponse("admin_only.html", {"request": request, "username": current_user.username})
