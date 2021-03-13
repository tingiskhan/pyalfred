from . import Base
from sqlalchemy import Column, String, Integer, Enum as EnumCol, Date, ForeignKey
from sqlalchemy.orm import relationship
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

    attachments = relationship("TaskAttachment")


class TaskAttachment(Base):
    __tablename__ = "task_attachment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey(Task.id), nullable=False)
    location = Column(String, nullable=False)
