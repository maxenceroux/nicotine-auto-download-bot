import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Message, HistorySongs, Show
import datetime
import pytz


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

    def get_medial_file_path_by_title(self, title):
        query = f"SELECT path FROM media_file WHERE title like ?"
        self.cursor.execute(query, ("%" + title + "%",))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def track_exists(self, title):
        query = f"SELECT path FROM media_file WHERE title like ?"
        self.cursor.execute(query, ("%" + title + "%",))
        result = self.cursor.fetchone()
        if result:
            return True
        return False

    def get_track_info_by_path(self, path):
        query = f"SELECT title, artist FROM media_file WHERE path = ?"
        self.cursor.execute(query, (path,))
        result = self.cursor.fetchone()
        return result if result else None

    def album_exists(self, album_name):
        query = "SELECT path FROM media_file WHERE album LIKE ?"
        self.cursor.execute(query, ("%" + album_name + "%",))
        result = self.cursor.fetchone()
        if result:
            return True
        return False

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
            created_at=datetime.datetime.utcnow().replace(tzinfo=pytz.utc),
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

    def is_new_song(self, title: str, artist: str):
        last_song = (
            self.session.query(HistorySongs)
            .order_by(HistorySongs.played_at.desc())
            .first()
        )
        if not last_song:
            return True
        if last_song.title == title and last_song.artist == artist:
            return False
        else:
            return True

    def add_to_history_songs(
        self, title: str, artist: str, description: str, artist_image: str
    ):
        last_three_songs = (
            self.session.query(HistorySongs)
            .order_by(HistorySongs.played_at.desc())
            .all()
        )
        if len(last_three_songs) == 3:
            self.session.delete(last_three_songs[-1])

        new_song = HistorySongs(
            title=title,
            artist=artist,
            description=description,
            artist_image=artist_image,
            played_at=datetime.datetime.utcnow().replace(tzinfo=pytz.utc),
        )
        self.session.add(new_song)
        self.session.commit()
        return new_song

    def get_tracks(self):
        tracks = (
            self.session.query(HistorySongs)
            .order_by(HistorySongs.played_at.desc())
            .all()
        )
        return tracks

    def create_show(
        self,
        start_time: datetime.datetime,
        author: str,
        name: str,
        playlist_url: str,
        description: str,
        ig_url: str = None,
        bc_url: str = None,
        sc_url: str = None,
    ):
        show = (
            self.session.query(Show)
            .filter(Show.start_time == start_time)
            .first()
        )
        if show:
            return False
        new_show = Show(
            start_time=start_time,
            author=author,
            name=name,
            playlist_url=playlist_url,
            description=description,
            ig_url=ig_url,
            bandcamp_url=bc_url,
            soundcloud_url=sc_url,
            created_at=datetime.datetime.now(),
        )
        self.session.add(new_show)
        self.session.commit()
        return new_show

    def set_show_playlist_path(self, start_time: datetime.datetime, path: str):
        show = (
            self.session.query(Show)
            .filter(Show.start_time == start_time)
            .first()
        )
        if show:
            show.playlist_path = path
            self.session.commit()
        return show

    def get_shows(self):
        shows = (
            self.session.query(Show)
            .filter(
                Show.start_time
                >= datetime.datetime.now() + datetime.timedelta(days=-1),
                Show.start_time
                <= datetime.datetime.now() + datetime.timedelta(days=7),
                Show.playlist_path != None,
            )
            .all()
        )
        return shows

    def get_current_show(self):
        now = datetime.datetime.now()
        one_hour_ago = now - datetime.timedelta(hours=1)
        show = (
            self.session.query(Show)
            .filter(
                Show.start_time >= one_hour_ago,
                Show.start_time
                <= datetime.datetime.now() + datetime.timedelta(hours=1),
                Show.playlist_path != None,
            )
            .first()
        )
        if show:
            return show
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
