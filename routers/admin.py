from fastapi import APIRouter, Request, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

from database import SessionLocal, get_db
from models import AdminUsers, Tasks

router = APIRouter()

templates = Jinja2Templates(directory="templates/admin")


@router.get("/")
async def index(request: Request, db: Session = Depends(get_db)):
    tasks = db.query(Tasks).all()
    #  Получаем список заявок пользователя сессии...
    return templates.TemplateResponse("мои_задачи.html", {"request": request, "tasks": tasks})


@router.get("/tasks")
async def tasks(request: Request, db: Session = Depends(get_db)):
    tasks = db.query(Tasks).all()
    #  Получаем список заявок пользователя сессии...
    return templates.TemplateResponse("заявки_в_техподдержку.html", {"request": request, "tasks": tasks})


@router.get("/users")
async def users(request: Request, db: Session = Depends(get_db)):
    admins = db.query(AdminUsers).all()
    #  admins = get_admin_users(db)
    print(admins)
    return templates.TemplateResponse("пользователи.html", {"request": request, "admins": admins})


@router.get("/user/{admin_id}")
async def user_id(request: Request, admin_id: int, db: Session = Depends(get_db)):
    # Получаем пользователя из базы данных
    user = db.query(AdminUsers).filter(AdminUsers.id == admin_id).first()

    # Если пользователь не найден, возвращаем ошибку 404
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Возвращаем данные пользователя
    return templates.TemplateResponse("admin_page.html", {"request": request, "user": user})
