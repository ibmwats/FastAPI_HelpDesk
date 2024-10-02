# models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Boolean, JSON, Table
from sqlalchemy.orm import relationship
from database import Base
import configparser

# Чтение настроек из settings.ini
config = configparser.ConfigParser()
config.read('settings.ini')

# Роли пользователей и статусы заявок
roles = config.get('settings', 'roles').split(',')
request_statuses = config.get('settings', 'request_statuses').split(',')
equipment_justification = config.get('settings', 'equipment_justification').split(',')
tariffs = config.get('settings', 'tariffs').split(',')

# Промежуточная таблица для связи "многие ко многим" между Task_equipment и Oborudovanie
task_equipment_oborudovanie = Table(
    'task_equipment_oborudovanie',
    Base.metadata,
    Column('task_equipment_id', Integer, ForeignKey('task_equipment.id'), primary_key=True),
    Column('oborudovanie_id', Integer, ForeignKey('oborudovanie.id'), primary_key=True)
)

# Промежуточная таблица для связи "многие ко многим" между Task_Universal и Services
task_universal_services = Table(
    'task_universal_services',
    Base.metadata,
    Column('task_universal_id', Integer, ForeignKey('task_universal.id'), primary_key=True),
    Column('services_id', Integer, ForeignKey('services.id'), primary_key=True)
)


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    name = Column(String, nullable=False)
    patronymic = Column(String, nullable=True)
    tel_stationary = Column(String, nullable=True)
    tel_mobile = Column(String, nullable=True)
    building = Column(String, nullable=True)
    cabinet = Column(String, nullable=True)
    last_entry = Column(DateTime, default=func.now())
    last_ip = Column(String, nullable=True)
    dostup = Column(String, default='пользователь', nullable=True)

    # Новая связь с отделом, где пользователь состоит
    otdel_id = Column(Integer, ForeignKey('otdel.id'), nullable=True)
    otdel = relationship("Otdel", back_populates="users", foreign_keys=[otdel_id])

    # Связь: один пользователь может быть начальником многих отделов
    otdel_nachalnik = relationship("Otdel", foreign_keys="[Otdel.nachalnik_id]", back_populates="nachalnik")

    # Связь: один пользователь может быть заместителем в нескольких отделах
    otdel_zam = relationship("Otdel", foreign_keys="[Otdel.zam_id]", back_populates="zam")

    # Связь: один пользователь может быть зам. ген. директора в нескольких отделах
    otdel_zgd = relationship("Otdel", foreign_keys="[Otdel.zgd_id]", back_populates="zgd")

    # Связь с задачами
    tasks_created = relationship("Task", back_populates="user_create")
    tasks_eq_created = relationship("Task_equipment", foreign_keys="[Task_equipment.user_create_id]", back_populates="user_create")
    tasks_eq_user_admin = relationship("Task_equipment", foreign_keys="[Task_equipment.user_admin_id]", back_populates="user_admin")
    tasks_universal_created = relationship("Task_Universal", foreign_keys="[Task_Universal.user_create_id]", back_populates="user_create")
    tasks_universal_user_admin = relationship("Task_Universal", foreign_keys="[Task_Universal.user_admin_id]", back_populates="user_admin")


class Otdel(Base):
    __tablename__ = 'otdel'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")

    # Добавляем связь с пользователями, состоящими в отделе
    users = relationship("User", back_populates="otdel", foreign_keys="[User.otdel_id]")

    # Начальник и заместители
    nachalnik_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    zam_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    zgd_id = Column(Integer, ForeignKey('user.id'), nullable=True)

    nachalnik = relationship("User", foreign_keys=[nachalnik_id], back_populates="otdel_nachalnik")
    zam = relationship("User", foreign_keys=[zam_id], back_populates="otdel_zam")
    zgd = relationship("User", foreign_keys=[zgd_id], back_populates="otdel_zgd")


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # Добавляем отношение для обратной связи с Task
    tasks = relationship("Task", back_populates="category")


class Task(Base):
    __tablename__ = 'task'

    id = Column(Integer, primary_key=True, index=True)
    tel = Column(String)  # Телефон
    theme = Column(String)  # Тема от пользователя
    location = Column(String)  # Местоположение
    text = Column(String)  # Основной текст заявки
    date_create = Column(DateTime, default=func.now())
    date_of_change = Column(DateTime, nullable=True)
    comments = Column(String)
    comments_cit_only = Column(String, default=None)
    comments_user = Column(String, default=None)
    logs = Column(String)  # Логирование действий пользователей
    ip_requests = Column(String)

    # Связь с таблицей Category
    category_id = Column(Integer, ForeignKey('category.id'), nullable=True)

    # Определение отношений
    category = relationship("Category", back_populates="tasks")

    # Связь с таблицей User (кто создал заявку)
    user_create_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    # Определение отношения с таблицей User
    user_create = relationship("User", back_populates="tasks_created")


class Task_equipment(Base):
    __tablename__ = 'task_equipment'

    id = Column(Integer, primary_key=True, index=True)

    # Связь с таблицей User (кто создал заявку)
    user_create_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user_admin_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    # Определение отношения с таблицей User
    user_create = relationship("User", foreign_keys=[user_create_id], back_populates="tasks_eq_created")
    user_admin = relationship("User", foreign_keys=[user_admin_id], back_populates="tasks_eq_user_admin")

    obosnovanie = Column(String, nullable=False)
    fio = Column(String, nullable=False)  # Для кого создаётся заявка
    doljonost = Column(String, nullable=False)
    geo = Column(String, nullable=False)

    date_create = Column(DateTime, default=func.now())
    date_of_change = Column(DateTime, nullable=True)
    status = Column(String, nullable=True)
    date_execution = Column(DateTime, nullable=True)

    # Поля комментариев
    comment_for_admin = Column(String, nullable=True)
    comment_ruk = Column(String, nullable=True)
    comment_admin_zgd_admin = Column(String, nullable=True)
    comment_admin_zgd = Column(String, nullable=True)
    comment_admin_for_all = Column(String, nullable=True)

    # Связь "многие ко многим" с таблицей Oborudovanie
    oborudovanie = relationship("Oborudovanie", secondary=task_equipment_oborudovanie, back_populates="task_equipment")

    other_equipment = Column(String, nullable=True)


class Oborudovanie(Base):
    __tablename__ = 'oborudovanie'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default=False, nullable=False)

    # Связь "многие ко многим" с таблицей Task_equipment
    task_equipment = relationship("Task_equipment", secondary=task_equipment_oborudovanie, back_populates="oborudovanie")


class Task_Universal(Base):
    __tablename__ = 'task_universal'

    id = Column(Integer, primary_key=True, index=True)

    # Связь с таблицей User (кто создал заявку)
    user_create_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user_create = relationship("User", foreign_keys=[user_create_id], back_populates="tasks_universal_created")

    # Связь с таблицей User (администратор заявки)
    user_admin_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user_admin = relationship("User", foreign_keys=[user_admin_id], back_populates="tasks_universal_user_admin")

    fio = Column(String, nullable=False)  # Для кого создаётся заявка
    doljonost = Column(String, nullable=False)

    # Поля комментариев
    comment_for_admin = Column(String, nullable=True)
    comment_ruk = Column(String, nullable=True)
    comment_admin_zgd_admin = Column(String, nullable=True)
    comment_admin_zgd = Column(String, nullable=True)
    comment_admin_for_all = Column(String, nullable=True)

    internet_is = Column(Boolean, default=False, nullable=True)
    corp_svyaz = Column(Boolean, default=False, nullable=True)

    date_create = Column(DateTime, default=func.now())
    date_of_change = Column(DateTime, nullable=True)
    status = Column(String, nullable=True)
    date_execution = Column(DateTime, nullable=True)

    # Связь "многие ко многим" с таблицей Services
    services = relationship("Services", secondary=task_universal_services, back_populates="task_universal")


class Services(Base):
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default=False, nullable=False)

    # Связь "многие ко многим" с таблицей Task_Universal
    task_universal = relationship("Task_Universal", secondary=task_universal_services, back_populates="services")
