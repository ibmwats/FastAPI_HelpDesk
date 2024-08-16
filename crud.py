from sqlalchemy.orm import Session
from models import AdminUsers
from schemas import SAdminUserCreate


def get_admin_users(db: Session):
    return db.query(AdminUsers).all()


