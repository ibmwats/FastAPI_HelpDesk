from sqlalchemy.orm import Session
from models import Users
from schemas import SAdminUserCreate


def get_admin_users(db: Session):
    return db.query(Users).all()


