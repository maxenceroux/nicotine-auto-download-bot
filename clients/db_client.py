import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Message
import datetime


class DBClient:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self

    def get_media_file_path(self, id):
        query = "SELECT path FROM media_file WHERE id = ?"
        self.cursor.execute(query, (id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.conn.close()


class RaxdioDB:
    def __init__(self, db_url: str) -> None:
        self.db = create_engine(db_url)
        self.session = sessionmaker(self.db)()

    def insert_user(self, username: str):
        db_user = User(username=username)
        user = (
            self.session.query(User).filter(User.username == username).first()
        )
        if not user:
            self.session.add(db_user)
            self.session.commit()
        return db_user

    def insert_message(self, username: str, message: str):
        db_message = Message(
            username=username,
            content=message,
            created_at=datetime.datetime.now(),
        )
        self.session.add(db_message)
        self.session.commit()
        return db_message

    def get_messages(self):
        messages = (
            self.session.query(Message)
            .order_by(Message.created_at.asc())
            .limit(200)
            .all()
        )
        results = []
        for message in messages:
            results.append(
                {
                    "username": message.username,
                    "content": message.content,
                    "created_at": message.created_at,
                }
            )

        return results

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
