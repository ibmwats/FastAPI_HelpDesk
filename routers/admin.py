from fastapi import APIRouter, Request, Depends, HTTPException, Form, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from starlette.templating import Jinja2Templates

from auth import get_current_user, hash_password
from database import get_db
from models import User, Task, roles, Otdel, Category
from routers.func import fetch_otdels, fetch_categories

router = APIRouter()
templates = Jinja2Templates(directory="templates/admin")


async def access_check(current_user: User = Depends(get_current_user)):
    if current_user.dostup not in ['админ', 'супер_админ']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешен только администраторам."
        )
    return current_user


@router.get("/")
async def index(request: Request,
                db: AsyncSession = Depends(get_db),
                current_user: User = Depends(access_check)):
    return templates.TemplateResponse("мои_задачи.html", {"request": request, "current_user": current_user})


@router.get("/users")
async def users(request: Request,
                db: AsyncSession = Depends(get_db),
                current_user: User = Depends(access_check)):
    try:
        result = await db.execute(select(User).options(joinedload(User.otdel)))
        users = result.scalars().all()
        return templates.TemplateResponse("все_пользователи.html", {"request": request, "users": users})
    except SQLAlchemyError as e:
        return {"Ошибка БД": f"{e}"}


@router.get("/user/{user_id}")
async def get_user(request: Request, user_id: int, db: AsyncSession = Depends(get_db),
                   current_user: User = Depends(access_check)):
    try:
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()

        result = await db.execute(select(Otdel))
        otdels = result.scalars().all()

        return templates.TemplateResponse("пользователь_обновление.html", {"request": request,
                                                                           "user": user,
                                                                           "roles": roles,
                                                                           "otdels": otdels})
    except SQLAlchemyError as e:
        # Логирование ошибки и возврат сообщения пользователю
        print(f"Ошибка базы данных: {e}")


@router.post("/user/{user_id}")
async def update_user(
        request: Request,
        user_id: int,
        username: str = Form(...),
        surname: str = Form(...),
        name: str = Form(...),
        patronymic: str = Form(...),
        tel_stationary: str = Form(...),
        tel_mobile: str = Form(...),
        building: str = Form(...),
        cabinet: str = Form(...),
        dostup: str = Form(...),
        otdel_id: int = Form(None),
        nachalnik: int = Form(None),
        zam: int = Form(None),
        zgd: int = Form(None),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(access_check)
):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        # Обновление данных пользователя
        user.username = username
        user.surname = surname
        user.name = name
        user.patronymic = patronymic
        user.tel_stationary = tel_stationary
        user.tel_mobile = tel_mobile
        user.building = building
        user.cabinet = cabinet
        user.dostup = dostup

        # Обновление отделов
        if otdel_id:
            result = await db.execute(select(Otdel).where(Otdel.id == otdel_id))
            user.otdel = result.scalar_one_or_none()
        if nachalnik:
            result = await db.execute(select(Otdel).where(Otdel.id == nachalnik))
            user.otdel_nachalnik = result.scalar_one_or_none()
        if zam:
            result = await db.execute(select(Otdel).where(Otdel.id == zam))
            user.otdel_zam = result.scalar_one_or_none()
        if zgd:
            result = await db.execute(select(Otdel).where(Otdel.id == zgd))
            user.otdel_zgd = result.scalar_one_or_none()

        await db.commit()

        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()

        result = await db.execute(select(Otdel))
        otdels = result.scalars().all()

        message_type = "success"
        message = f"Пользователь {user.surname} {user.name} {user.patronymic} успешно обновлен"

        return templates.TemplateResponse("пользователь_обновление.html", {"request": request,
                                                                           "message_type": message_type,
                                                                           "message": message,
                                                                           "user": user,
                                                                           "roles": roles,
                                                                           "otdels": otdels})

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при обновлении пользователя")


@router.post("/user/{user_id}/change-password")
async def update_user(
        request: Request,
        user_id: int,
        new_password: str = Form(...),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(access_check)
):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        pass_hash = await hash_password(new_password)
        # Обновление данных пользователя
        user.password = pass_hash

        await db.commit()

        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()

        result = await db.execute(select(Otdel))
        otdels = result.scalars().all()

        message_type = "success"
        message = f"Пользователь {user.surname} {user.name} {user.patronymic} успешно обновлен"

        return templates.TemplateResponse("пользователь_обновление.html", {"request": request,
                                                                           "message_type": message_type,
                                                                           "message": message,
                                                                           "user": user,
                                                                           "roles": roles,
                                                                           "otdels": otdels})

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при обновлении пользователя")


@router.get("/otdels")
async def get_otdels(request: Request, db: AsyncSession = Depends(get_db),
                     current_user: User = Depends(access_check)):
    try:
        otdels = await fetch_otdels(db)
        return templates.TemplateResponse("все_отделы.html", {"request": request, "otdels": otdels})

    except Exception as e:
        return {"Ошибка БД": str(e)}


@router.post("/otdels")
async def add_otdel_p(request: Request,
                      name: str = Form(...),
                      description: str = Form(default=""),
                      db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(access_check)):
    try:
        # Проверяем, существует ли домен
        result = await db.execute(select(Otdel).filter(Otdel.name == name))
        otdel = result.scalars().first()
        otdels = await fetch_otdels(db)
        if otdel:
            message = '<strong>Отдел уже существует!</strong>'
            message_type = f"danger"
            return templates.TemplateResponse("все_отделы.html", {"request": request,
                                                                  "otdels": otdels,
                                                                  "message_type": message_type,
                                                                  "message": message})
        # Если отдел не существует, добавляем его
        new_otdel = Otdel(
            name=name,
            description=description
        )
        db.add(new_otdel)
        await db.commit()

        otdels = await fetch_otdels(db)

        # Сообщение об успешном добавлении домена
        message = "<strong>Поздравляем!</strong> Вы успешно добавили отдел!"
        message_type = f"success"
        return templates.TemplateResponse("все_отделы.html", {"request": request,
                                                              "otdels": otdels,
                                                              "message_type": message_type,
                                                              "message": message})

    except SQLAlchemyError as e:
        # Логирование ошибки и возврат сообщения пользователю
        print(f"Ошибка базы данных: {e}")
        message = "<strong>Ошибка</strong> при добавлении отдела. Попробуйте еще раз позже."
        message_type = f"danger"
        return templates.TemplateResponse("все_отделы.html", {"request": request,
                                                              "message_type": message_type,
                                                              "message": message})


@router.get("/otdel/{otdel_id}")
async def get_otdel(request: Request, otdel_id: int, db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(access_check)):
    try:
        result = await db.execute(select(Otdel).filter(Otdel.id == otdel_id))
        otdel = result.scalars().first()

        result = await db.execute(select(User))
        users = result.scalars().all()

        return templates.TemplateResponse("отдел_обновление.html", {"request": request,
                                                                    "otdel": otdel,
                                                                    "users": users})
    except SQLAlchemyError as e:
        # Логирование ошибки и возврат сообщения пользователю
        print(f"Ошибка базы данных: {e}")


@router.get("/otdel/{otdel_id}/delete")
async def delete_otdel(
        request: Request,
        otdel_id: int, db: AsyncSession = Depends(get_db),
        current_user: User = Depends(access_check)
):
    try:
        result = await db.execute(select(Otdel).where(Otdel.id == otdel_id))
        otdel = result.scalar_one_or_none()

        if otdel is None:
            raise HTTPException(status_code=404, detail="Отдел не найден")

        # Удаляем отдел
        await db.delete(otdel)
        await db.commit()

        otdels = await fetch_otdels(db)
        message = "<strong>Успешно</strong> удалили отдел."
        message_type = f"success"
        return templates.TemplateResponse("все_отделы.html", {"request": request,
                                                              "otdels": otdels,
                                                              "message_type": message_type,
                                                              "message": message})

    except SQLAlchemyError as e:
        # Логирование ошибки и возврат сообщения пользователю
        print(f"Ошибка базы данных: {e}")
        message = "<strong>Ошибка</strong> при удалении отдела. Попробуйте еще раз позже."
        message_type = f"danger"
        return templates.TemplateResponse("все_отделы.html", {"request": request,
                                                              "message_type": message_type,
                                                              "message": message})


@router.post("/otdel/{otdel_id}")
async def update_otdel(
        request: Request,
        otdel_id: int,
        name: str = Form(...),
        description: str = Form(default=""),
        nachalnik_id: int = Form(None),
        zam_id: int = Form(None),
        zgd_id: int = Form(None),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(access_check)
):
    try:
        # Получаем отдел по ID
        result = await db.execute(select(Otdel).where(Otdel.id == otdel_id))
        otdel = result.scalar_one_or_none()

        if otdel is None:
            raise HTTPException(status_code=404, detail="Отдел не найден")

        # Обновляем данные отдела
        otdel.name = name
        otdel.description = description
        otdel.nachalnik_id = nachalnik_id
        otdel.zam_id = zam_id
        otdel.zgd_id = zgd_id

        # Сохраняем изменения в БД
        await db.commit()

        result = await db.execute(select(User))
        all_users = result.scalars().all()

        result = await db.execute(select(Otdel).filter(Otdel.id == otdel_id))
        update_otdel = result.scalars().first()

        message = f"Отдел {update_otdel.name} успешно обновлен"
        message_type = f"success"

        return templates.TemplateResponse("отдел_обновление.html", {"request": request,
                                                                    "otdel": update_otdel,
                                                                    "message": message,
                                                                    "message_type": message_type,
                                                                    "users": all_users})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def categories(request: Request, db: AsyncSession = Depends(get_db),
                     current_user: User = Depends(access_check)):
    try:
        all_categories = await fetch_categories(db)
        return templates.TemplateResponse("категории.html", {"request": request, "categories": all_categories})

    except Exception as e:
        return {"Ошибка БД": str(e)}


@router.post("/categories")
async def add_categories(request: Request,
                         name: str = Form(...),
                         description: str = Form(default=""),
                         db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(access_check)):
    try:
        # Проверяем, существует ли домен
        result = await db.execute(select(Category).filter(Category.name == name))
        category = result.scalars().first()

        if category:
            all_categories = await fetch_categories(db)

            message = '<strong>Категория уже существует!</strong>'
            message_type = f"danger"
            return templates.TemplateResponse("категории.html", {"request": request,
                                                                 "categories": all_categories,
                                                                 "message_type": message_type,
                                                                 "message": message})
        # Если отдел не существует, добавляем его
        new_cat = Category(
            name=name,
            description=description
        )
        db.add(new_cat)
        await db.commit()

        all_categories = await fetch_categories(db)

        # Сообщение об успешном добавлении домена
        message = "<strong>Поздравляем!</strong> Вы успешно добавили категорию!"
        message_type = f"success"
        return templates.TemplateResponse("категории.html", {"request": request,
                                                             "categories": all_categories,
                                                             "message_type": message_type,
                                                             "message": message})

    except SQLAlchemyError as e:
        # Логирование ошибки и возврат сообщения пользователю
        print(f"Ошибка базы данных: {e}")
        message = "<strong>Ошибка</strong> при добавлении отдела. Попробуйте еще раз позже."
        message_type = f"danger"
        return templates.TemplateResponse("категории.html", {"request": request,
                                                             "message_type": message_type,
                                                             "message": message})
