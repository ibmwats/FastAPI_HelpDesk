from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from crud import get_admin_users
from database import engine, SessionLocal, Base
from models import AdminUsers, Users, Tasks, StatusTask, File, Categories
from schemas import SAdminUserCreate, SUserCreate, SAdmin

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def read_root(request: Request, db: Session = Depends(get_db)):
    admins = db.query(AdminUsers).all()
    #  admins = get_admin_users(db)
    return templates.TemplateResponse("index.html", {"request": request, "admins": admins})


@app.post("/admin_users/")
async def create_admin_user(user: SAdminUserCreate, db: Session = Depends(get_db)):
    db_user = AdminUsers(username=user.username, password=user.password, name=user.name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/admin_create")
async def create_admin(
        username: str = Form(...),
        password: str = Form(...),
        name: str = Form(...),
        db: Session = Depends(get_db)
):
    db_user = AdminUsers(username=username, password=password, name=name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return RedirectResponse(url="/", status_code=303)


@app.get("/admin/{admin_id}")
async def get_user(request: Request, admin_id: int, db: Session = Depends(get_db)):
    # Получаем пользователя из базы данных
    user = db.query(AdminUsers).filter(AdminUsers.id == admin_id).first()

    # Если пользователь не найден, возвращаем ошибку 404
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Возвращаем данные пользователя
    return templates.TemplateResponse("admin_page.html", {"request": request, "user": user})


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


@app.get('/index')
async def index(request: Request):
    test = 'test text'
    return templates.TemplateResponse('index.html', {"request": request})
