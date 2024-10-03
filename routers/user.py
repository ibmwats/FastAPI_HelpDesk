import os
from fastapi import APIRouter, Request, Depends, HTTPException, Form, status, UploadFile, File
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy import func

from auth import get_current_user, hash_password
from database import get_db
from models import User, Task
from routers.func import fetch_categories, fetch_task_user, get_task_count

router = APIRouter()
templates = Jinja2Templates(directory="templates/user")
UPLOAD_DIR = "static/uploaded_files"


async def access_check(current_user: User = Depends(get_current_user)):
    if current_user.dostup not in ['пользователь']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешен только пользователей."
        )
    return current_user


@router.get("/")
async def index(request: Request,
                db: AsyncSession = Depends(get_db),
                current_user: User = Depends(access_check)):
    return templates.TemplateResponse("главная.html", {"request": request, "current_user": current_user})


@router.get("/create-task")
async def task_create(request: Request,
                      db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(access_check)):
    all_categories = await fetch_categories(db)

    return templates.TemplateResponse("создать_заявку.html", {"request": request,
                                                              "current_user": current_user,
                                                              "categories": all_categories})


@router.post("/create-task")
async def create_task(request: Request,
                      tel: str = Form(...),
                      theme: str = Form(...),
                      location: str = Form(...),
                      text: str = Form(...),
                      category_id: int = Form(...),
                      files: list[UploadFile] = File(None),
                      db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(access_check)):
    try:
        # Создание новой записи заявки
        last_ip = request.client.host
        new_task = Task(
            tel=tel,
            theme=theme,
            location=location,
            text=text,
            category_id=category_id,
            user_create_id=current_user.id,
            ip_requests=last_ip
        )
        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)

        # Обработка файлов
        if files:
            file_urls = []
            task_id = new_task.id
            task_upload_dir = os.path.join(UPLOAD_DIR, str(task_id))
            os.makedirs(task_upload_dir, exist_ok=True)

            for file in files:
                # Путь для сохранения файла в папку с ID заявки
                file_path = os.path.join(task_upload_dir, file.filename)

                # Сохраняем файл на сервер
                with open(file_path, "wb") as buffer:
                    buffer.write(await file.read())

                # Формируем ссылку для скачивания
                file_url = f"/static/uploaded_files/{task_id}/{file.filename}"
                file_urls.append(file_url)

            # Добавляем ссылки на файлы в текст заявки
            new_task.text += "\n\nПрикрепленные файлы:\n" + "\n".join(file_urls)

            # Сохраняем изменения в базе данных
            await db.commit()

        # Сообщение об успешном добавлении заявки
        message = "<strong>Заявка успешно создана!</strong>"
        message_type = "success"
        return templates.TemplateResponse("создать_заявку.html", {
            "request": request,
            "current_user": current_user,
            "message": message,
            "message_type": message_type
        })

    except SQLAlchemyError as e:
        # Логирование ошибки и вывод сообщения пользователю
        print(f"Ошибка базы данных: {e}")
        message = "<strong>Ошибка</strong> при создании заявки. Попробуйте еще раз позже."
        message_type = "danger"
        return templates.TemplateResponse("создать_заявку.html", {
            "request": request,
            "current_user": current_user,
            "message": message,
            "message_type": message_type
        })


@router.get("/tasks")
async def task_create_equipment(request: Request,
                                db: AsyncSession = Depends(get_db),
                                current_user: User = Depends(access_check)):
    my_tasks = await fetch_task_user(db, current_user.id)

    return templates.TemplateResponse("список_заявок.html", {"request": request,
                                                             "current_user": current_user,
                                                             "tasks": my_tasks})


@router.get("/create-task-equipment")
async def task_create_equipment(request: Request,
                                db: AsyncSession = Depends(get_db),
                                current_user: User = Depends(access_check)):
    return templates.TemplateResponse("создать_заявку.html", {"request": request, "current_user": current_user})


@router.get("/create-task-universal")
async def task_create_universal(request: Request,
                                db: AsyncSession = Depends(get_db),
                                current_user: User = Depends(access_check)):
    return templates.TemplateResponse("создать_заявку.html", {"request": request, "current_user": current_user})
