from . import Base
from sqlalchemy import Column, String, Integer, Enum as EnumCol, Date
from enum import Enum


class TaskType(Enum):
    Note = "Note"
    Task = "Task"


class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    finished_by = Column(Date, nullable=False)
    type = Column(EnumCol(TaskType, create_constraint=False, native_enum=False), nullable=False)
