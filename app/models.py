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


class HistorySongs(Base):
    __tablename__ = "history_songs"
    id = Column(Integer, primary_key=True, index=True)
    played_at = Column(DateTime(timezone=True))
    title = Column(String)
    artist = Column(String)
    artist_image = Column(String)
    description = Column(String)


class Show(Base):
    __tablename__ = "shows"
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime(timezone=True))
    author = Column(String)
    name = Column(String)
    playlist_url = Column(String)
    playlist_path = Column(String)
    description = Column(String)
    ig_url = Column(String)
    bandcamp_url = Column(String)
    soundcloud_url = Column(String)
