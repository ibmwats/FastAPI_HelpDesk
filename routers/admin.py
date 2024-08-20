from fastapi import APIRouter, Request, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from database import SessionLocal, get_db
from models import Users, Tasks, UserType
from schemas import SAdminUserCreate, SUserTypeCreate

router = APIRouter()

templates = Jinja2Templates(directory="templates/admin")


@router.get("/")
async def index(request: Request, db: Session = Depends(get_db)):
    tasks = db.query(Tasks).all()
    #  Получаем список заявок пользователя сессии...
    return templates.TemplateResponse("мои_задачи.html", {"request": request, "tasks": tasks})


@router.get("/create_type_user")
async def type_user(request: Request, db: Session = Depends(get_db)):
    types = db.query(UserType).all()
    #  Получаем список заявок пользователя сессии...
    return templates.TemplateResponse("создать_типы_пользователей.html", {"request": request, "types": types})


@router.post("/create_type_user")
async def create_user_type(type_name: str = Form(...), description: str = Form(...), db: Session = Depends(get_db)):
    new_user_type = UserType(type_name=type_name, description=description)
    db.add(new_user_type)
    db.commit()
    db.refresh(new_user_type)
    return RedirectResponse(url="./create_type_user", status_code=303)


@router.get("/create_user")
async def index(request: Request, db: Session = Depends(get_db), created_user_id: int = None):
    types = db.query(UserType).all()

    created_user = None
    if created_user_id:
        created_user = db.query(Users).filter(Users.id == created_user_id).first()
    return templates.TemplateResponse("создать_пользователя.html", {"request": request,
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
    new_user = Users(username=username, password=password, name_0=name_0, name_1=name_1, name_2=name_2,
                     tel=tel, tel_m=tel_m, division=division, building=building, cabinet=cabinet,
                     user_type_id=user_type_id)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url=f"./create_user?created_user_id={new_user.id}", status_code=303)


@router.get("/tasks")
async def tasks(request: Request, db: Session = Depends(get_db)):
    tasks = db.query(Tasks).all()
    #  Получаем список заявок пользователя сессии...
    return templates.TemplateResponse("заявки_в_техподдержку.html", {"request": request, "tasks": tasks})


@router.get("/users")
async def users(request: Request, db: Session = Depends(get_db)):
    admins = db.query(Users).all()
    #  admins = get_admin_users(db)
    print(admins)
    return templates.TemplateResponse("пользователи.html", {"request": request, "admins": admins})


@router.get("/user/{admin_id}")
async def user_id(request: Request, admin_id: int, db: Session = Depends(get_db)):
    # Получаем пользователя из базы данных
    user = db.query(Users).filter(Users.id == admin_id).first()

    # Если пользователь не найден, возвращаем ошибку 404
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Возвращаем данные пользователя
    return templates.TemplateResponse("admin_page.html", {"request": request, "user": user})


'''
Тестовые функции


@router.post("/user_types/create")
async def create_user_type(type_name: str, description: str, db: Session = Depends(get_db)):
    new_user_type = UserType(type_name=type_name, description=description)
    db.add(new_user_type)
    db.commit()
    return {"message": "User Type created"}


@router.get("/users/create", response_class=HTMLResponse)
async def create_user_form(request: Request):
    user_types = db.query(UserType).all()  # Приведите соответствующий запрос для получения типов пользователей
    user_type_options = "".join(
        f'<option value="{user_type.id}">{user_type.type_name}</option>' for user_type in user_types)
    return f"""
    <html>
        <body>
            <h2>Create User</h2>
            <form action="/users/create" method="post">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username"><br><br>
                <label for="password">Password:</label>
                <input type="password" id="password" name="password"><br><br>
                <label for="name_0">Name (First):</label>
                <input type="text" id="name_0" name="name_0"><br><br>
                <label for="name_1">Name (Middle):</label>
                <input type="text" id="name_1" name="name_1"><br><br>
                <label for="name_2">Name (Last):</label>
                <input type="text" id="name_2" name="name_2"><br><br>
                <label for="tel">Phone:</label>
                <input type="text" id="tel" name="tel"><br><br>
                <label for="tel_m">Mobile Phone:</label>
                <input type="text" id="tel_m" name="tel_m"><br><br>
                <label for="division">Division:</label>
                <input type="text" id="division" name="division"><br><br>
                <label for="building">Building:</label>
                <input type="text" id="building" name="building"><br><br>
                <label for="cabinet">Cabinet:</label>
                <input type="text" id="cabinet" name="cabinet"><br><br>
                <label for="user_type_id">User Type:</label>
                <select id="user_type_id" name="user_type_id">
                    {user_type_options}
                </select><br><br>
                <input type="submit" value="Submit">
            </form>
        </body>
    </html>
    """


@router.post("/users/create")
async def create_user(username: str, password: str, name_0: str, name_1: str, name_2: str,
                      tel: str, tel_m: str, division: str, building: str, cabinet: str,
                      user_type_id: int, db: Session = Depends(get_db)):
    new_user = User(username=username, password=password, name_0=name_0, name_1=name_1, name_2=name_2,
                    tel=tel, tel_m=tel_m, division=division, building=building, cabinet=cabinet,
                    user_type_id=user_type_id)
    db.add(new_user)
    db.commit()
    return {"message": "User created"}
'''
