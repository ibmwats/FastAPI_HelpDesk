from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from sqlalchemy import func
from models import Otdel, Category, Task


async def fetch_otdels(db: AsyncSession):
    """Получаем список всех отделов с предзагрузкой связанных данных."""
    try:
        result = await db.execute(select(Otdel).options(
            selectinload(Otdel.nachalnik),
            selectinload(Otdel.zam),
            selectinload(Otdel.zgd),
            selectinload(Otdel.users)
        ))
        return result.scalars().all()
    except Exception as e:
        raise Exception(f"Ошибка при получении отделов: {str(e)}")


async def fetch_categories(db: AsyncSession):
    """Получаем список всех категорий"""
    try:
        result = await db.execute(select(Category))
        return result.scalars().all()
    except Exception as e:
        raise Exception(f"Ошибка при получении категорий: {str(e)}")


async def fetch_task_user(db: AsyncSession, user_id: int):
    """Получаем список всех заявок пользователя по id"""
    try:
        result = await db.execute(
            select(Task)
            .options(selectinload(Task.category))  # Загрузка связанных категорий
            .filter(Task.user_create_id == user_id)  # Фильтрация по user_create_id
        )
        return result.scalars().all()
    except Exception as e:
        raise Exception(f"Ошибка при получении категорий: {str(e)}")


async def get_task_count(db: AsyncSession, user_id: int):
    try:
        result = await db.execute(
            select(func.count(Task.id))  # Считаем количество задач
            .filter(
                Task.status.in_(["Новая", "Ожидает решения", "В работе", "Запланирована"]),  # Фильтруем по статусу
                Task.user_create_id == user_id  # Фильтруем по ID пользователя
            )
        )

        return result.scalar()
    except Exception as e:
        raise Exception(f"Ошибка при получении категорий: {str(e)}")
