from . import Base
from sqlalchemy import Column, String, Integer


class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)