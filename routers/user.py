from fastapi import APIRouter, Request, Depends, HTTPException, Form, status
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from auth import get_current_user, hash_password
from database import get_db
from models import Users, Tasks, UserType

router = APIRouter()
templates = Jinja2Templates(directory="templates/user")


@router.get("/")
async def index(request: Request,
                db: Session = Depends(get_db),
                current_user: Users = Depends(get_current_user)):
    print(current_user.user_type_relation.type_name)
    if current_user.user_type_relation.type_name == 'user':
        try:
            return templates.TemplateResponse("главная.html", {"request": request, "current_user": current_user})
        except HTTPException as exc:
            if exc.status_code == status.HTTP_303_SEE_OTHER:
                return RedirectResponse(url="/login")
            raise exc
    else:
        return {"Исключение": "Доступ только для пользователя!"}