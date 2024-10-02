from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from models import Otdel


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





