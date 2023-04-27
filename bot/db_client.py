import sqlite3


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
