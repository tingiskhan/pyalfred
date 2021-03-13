from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Enum as EnumCol, Date, ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum


class TaskType(Enum):
    Note = "Note"
    Task = "Task"


Base = declarative_base()


class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    finished_by = Column(Date, nullable=False)
    type = Column(EnumCol(TaskType, create_constraint=False, native_enum=False), nullable=False)


class TaskWithRelationShip(Base):
    __tablename__ = "task_with_relationship"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    finished_by = Column(Date, nullable=False)
    type = Column(EnumCol(TaskType, create_constraint=False, native_enum=False), nullable=False)

    attachments = relationship("Attachment")


class Attachment(Base):
    __tablename__ = "attchment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey(TaskWithRelationShip.id), nullable=False)
    location = Column(String, nullable=False)
