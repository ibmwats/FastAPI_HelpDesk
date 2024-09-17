from fastapi import APIRouter, Request, Depends, HTTPException, Form, status
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from auth import get_current_user, hash_password
from database import get_db
from models import Users, Tasks, UserType

router = APIRouter()
templates = Jinja2Templates(directory="templates/admin")


@router.get("/")
async def index(request: Request,
                db: Session = Depends(get_db),
                current_user: Users = Depends(get_current_user)):
    print(current_user.user_type_relation.type_name)
    if current_user.user_type_relation.type_name == 'admin' or current_user.user_type_relation.type_name == 'super_admin':
        try:
            tasks = db.query(Tasks).all()
            return templates.TemplateResponse("мои_задачи.html", {"request": request,
                                                                  "current_user": current_user,
                                                                  "tasks": tasks})
        except HTTPException as exc:
            if exc.status_code == status.HTTP_303_SEE_OTHER:
                return RedirectResponse(url="/login")
            raise exc
    else:
        return {"Исключение": "Доступ запрещен!"}


@router.get("/create_type_user")
async def type_user(request: Request,
                    db: Session = Depends(get_db),
                    current_user: Users = Depends(get_current_user)):
    types = db.query(UserType).all()
    #  Получаем список заявок пользователя сессии...
    return templates.TemplateResponse("создать_типы_пользователей.html", {"request": request,
                                                                          "current_user": current_user,
                                                                          "types": types})


@router.post("/create_type_user")
async def create_user_type(type_name: str = Form(...), description: str = Form(...), db: Session = Depends(get_db)):
    new_user_type = UserType(type_name=type_name, description=description)
    db.add(new_user_type)
    db.commit()
    db.refresh(new_user_type)
    return RedirectResponse(url="./create_type_user", status_code=303)


@router.get("/create_user")
async def index(request: Request,
                db: Session = Depends(get_db),
                current_user: Users = Depends(get_current_user),
                created_user_id: int = None):
    types = db.query(UserType).all()
    created_user = None
    if created_user_id:
        created_user = db.query(Users).filter(Users.id == created_user_id).first()
    return templates.TemplateResponse("создать_пользователя.html", {"request": request,
                                                                    "current_user": current_user,
                                                                    "types": types,
                                                                    "created_user": created_user})


@router.post("/create_user")
async def create_user(username: str = Form(...),
                      password: str = Form(...),
                      name_0: str = Form(...),
                      name_1: str = Form(...),
                      name_2: str = Form(...),
                      tel: str = Form(...),
                      tel_m: str = Form(...),
                      division: str = Form(...),
                      building: str = Form(...),
                      cabinet: str = Form(...),
                      user_type_id: str = Form(...),
                      db: Session = Depends(get_db)):
    pass_hash = hash_password(password)
    new_user = Users(username=username, password=pass_hash, name_0=name_0, name_1=name_1, name_2=name_2,
                     tel=tel, tel_m=tel_m, division=division, building=building, cabinet=cabinet,
                     user_type_id=user_type_id)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url=f"./create_user?created_user_id={new_user.id}", status_code=303)


@router.get("/tasks")
async def tasks(request: Request,
                db: Session = Depends(get_db),
                current_user: Users = Depends(get_current_user)):
    tasks = db.query(Tasks).all()
    #  Получаем список заявок пользователя сессии...
    return templates.TemplateResponse("заявки_в_техподдержку.html", {"request": request,
                                                                     "current_user": current_user,
                                                                     "tasks": tasks})


@router.get("/users")
async def users(request: Request,
                db: Session = Depends(get_db),
                current_user: Users = Depends(get_current_user)):
    admins = db.query(Users).all()
    #  admins = get_admin_users(db)
    print(admins)
    return templates.TemplateResponse("пользователи.html", {"request": request,
                                                            "current_user": current_user,
                                                            "admins": admins})


@router.get("/user/{admin_id}")
async def user_id(request: Request, admin_id: int,
                  db: Session = Depends(get_db),
                  current_user: Users = Depends(get_current_user)):
    # Получаем пользователя из базы данных
    user = db.query(Users).filter(Users.id == admin_id).first()

    # Если пользователь не найден, возвращаем ошибку 404
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Возвращаем данные пользователя
    return templates.TemplateResponse("admin_page.html", {"request": request,
                                                          "current_user": current_user,
                                                          "user": user})
