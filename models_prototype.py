from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PositionEnum(PyEnum):
    WORKER = "worker"
    DEPARTMENT_HEAD = "department_head"
    DEPUTY_HEAD = "deputy_head"
    DEPUTY_GENERAL_DIRECTOR = "deputy_general_director"
    DEPUTY_FINANCE_DIRECTOR = "deputy_finance_director"
    CIT_EMPLOYEE = "cit_employee"

# Модель для отделов
class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    head_id = Column(Integer, ForeignKey('employees.id'))  # Руководитель отдела
    deputy_id = Column(Integer, ForeignKey('employees.id'))  # Заместитель руководителя
    deputy_general_director_id = Column(Integer, ForeignKey('employees.id'))  # Заместитель генерального директора

    head = relationship("Employee", foreign_keys=[head_id])
    deputy = relationship("Employee", foreign_keys=[deputy_id])
    deputy_general_director = relationship("Employee", foreign_keys=[deputy_general_director_id])

# Модель для сотрудников
class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    position = Column(Enum(PositionEnum), nullable=False)  # Должность
    department_id = Column(Integer, ForeignKey('departments.id'))  # Связь с отделом

    department = relationship("Department", back_populates="employees")

# Модель для заявок на оборудование
class EquipmentRequest(Base):
    __tablename__ = "equipment_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey('employees.id'))  # Кто создал заявку
    description = Column(String, nullable=False)  # Описание оборудования
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")  # Статус заявки (например: pending, approved, rejected)

    employee = relationship("Employee")

# Модель для согласований заявки
class ApprovalStep(Base):
    __tablename__ = "approval_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey('equipment_requests.id'))  # Связь с заявкой
    approver_id = Column(Integer, ForeignKey('employees.id'))  # Кто согласовывает
    approved_at = Column(DateTime)  # Дата согласования
    status = Column(String, default="pending")  # Статус этапа (pending, approved, rejected)
    comment = Column(String, nullable=True)  # Комментарий к этапу согласования

    request = relationship("EquipmentRequest", back_populates="approval_steps")
    approver = relationship("Employee")

EquipmentRequest.approval_steps = relationship("ApprovalStep", back_populates="request")
