from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base


class AdminUsers(Base):
    __tablename__ = 'admin_users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    password = Column(String)
    name = Column(String)  # ФИО
    last_entry = Column(DateTime, default=func.now())

    tasks = relationship("Tasks", back_populates="user_spec")


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    password = Column(String)
    name_0 = Column(String)  # Ф
    name_1 = Column(String)  # И
    name_2 = Column(String)  # О
    tel = Column(String)  # Стационарный тел
    tel_m = Column(String)  # Мобильный тел
    division = Column(String)  # Подразделение
    building = Column(String)  # Здание
    cabinet = Column(String)  # Кабинет
    last_entry = Column(DateTime, default=func.now())
    last_ip = Column(String)
    user_type = Column(String)  # Тип пользователя(ЗГД/Обычный)

    tasks = relationship("Tasks", back_populates="user_create")


class Tasks(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, index=True)
    tel = Column(String)  # Телефон
    theme = Column(String)  # Тема от пользователя
    location = Column(String)  # Местоположение
    text = Column(String)  # Основной текст заявки
    date_create = Column(DateTime, default=func.now())
    date_of_change = Column(DateTime, nullable=True)
    comments = Column(String)
    logs = Column(String)  # Логирование действий пользователей

    category_id = Column(Integer, ForeignKey('categories.id'))  # Связь с таблицей категорий
    category = relationship("Categories", back_populates="tasks")

    files = relationship("File", back_populates="task")

    user_create_id = Column(Integer, ForeignKey('users.id'))  # Связь с таблицей users
    user_create = relationship("Users", back_populates="tasks")

    user_spec_id = Column(Integer, ForeignKey('admin_users.id'))  # Связь с таблицей UserAdmin
    user_spec = relationship("AdminUsers", back_populates="tasks")

    status_id = Column(Integer, ForeignKey('statustask.id'))  # Связь с таблицей статусов задач
    status = relationship("StatusTask", back_populates="tasks")


class StatusTask(Base):
    __tablename__ = 'statustask'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)

    tasks = relationship("Tasks", back_populates="status")


class File(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    task_id = Column(Integer, ForeignKey('tasks.id'))

    task = relationship("Tasks", back_populates="files")


class Categories(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

    tasks = relationship("Tasks", back_populates="category")
