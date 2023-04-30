from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    Boolean,
    Integer,
    String,
    DateTime,
    Float,
    Date,
    ForeignKey,
)


Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(
        String,
    )


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    content = Column(String)
    created_at = Column(DateTime(timezone=True))
