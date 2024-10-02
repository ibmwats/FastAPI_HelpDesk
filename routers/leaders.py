from fastapi import APIRouter, Request, Depends, HTTPException, Form, status
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from auth import get_current_user, hash_password
from database import get_db
from models import User

router = APIRouter()
templates = Jinja2Templates(directory="templates/leaders")


async def access_check(current_user: User = Depends(get_current_user)):
    if current_user.dostup not in ['згд']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешен только ЗГД."
        )
    return current_user


@router.get("/")
async def index(request: Request,
                db: Session = Depends(get_db),
                current_user: User = Depends(access_check)):
    return templates.TemplateResponse("главная.html", {"request": request, "current_user": current_user})
