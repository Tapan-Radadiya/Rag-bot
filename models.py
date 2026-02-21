from sqlalchemy import Uuid, Column, ForeignKey, Integer, String, TIMESTAMP
from pgvector.sqlalchemy import Vector
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class UserData(Base):
    __tablename__ = "user_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(TIMESTAMP, default=datetime.now())


class Document(Base):
    __tablename__ = "document"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_data.id"))
    text = Column(String)
    embedding = Column(Vector(384), index=True)
