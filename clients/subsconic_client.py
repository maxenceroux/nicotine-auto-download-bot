import requests
import hashlib
import xml.etree.ElementTree as ET
from unidecode import unidecode
from clients.db_client import DBClient
import os


class SubsonicClient:
    def __init__(
        self,
        user: str,
        password: str,
        salt: str,
        host: str,
        port: int,
        api_version: str,
    ) -> None:
        self.token = hashlib.md5(f"{password}{salt}".encode()).hexdigest()
        self.params = {
            "u": user,
            "v": api_version,
            "c": "my_api",
            "t": self.token,
            "s": salt,
        }
        self._base_url = f"http://{host}:{port}/rest"

    def get_playlist_id(self, playlist_name):
        url = f"{self._base_url}/getPlaylists"
        try:
            response = requests.get(url, params=self.params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        my_xml = response.content
        root = ET.fromstring(my_xml)
        for child in root:
            for subchild in child:
                if subchild.attrib["name"] == playlist_name:
                    return subchild.attrib["id"]
        return False

    def get_playlist_tracks(self, playlist_id: str):
        url = f"{self._base_url}/getPlaylist"
        params = self.params
        params["id"] = playlist_id
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        my_xml = response.content
        root = ET.fromstring(my_xml)
        playlist_tracks = []
        with DBClient("/db/music.db") as db_client:
            for child in root:
                for subchild in child:
                    file_path = db_client.get_media_file_path(
                        subchild.attrib["id"]
                    )
                    file_path = file_path.split("/music/")[1]
                    playlist_tracks.append(file_path)
        return playlist_tracks

    def get_artist_id(self, artist_name: str):
        url = f"{self._base_url}/getArtists"
        try:
            response = requests.get(url, params=self.params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        my_xml = response.content
        root = ET.fromstring(my_xml)
        for child in root:
            for subchild in child:
                for sub in subchild:
                    if unidecode(
                        sub.attrib["name"].lower().strip()
                    ) == unidecode(artist_name.lower().strip()):
                        return sub.attrib["id"]
        return None

    def get_artist_albums(self, artist_id: str):
        url = f"{self._base_url}/getArtist"
        params = self.params
        params["id"] = artist_id
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        my_xml = response.content
        root = ET.fromstring(my_xml)
        albums = []
        for child in root:
            for subchild in child:
                albums.append(subchild.attrib)
        return albums

    def get_album_tracks(self, album_id: str):
        url = f"{self._base_url}/getAlbum"
        params = self.params
        params["id"] = album_id
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        my_xml = response.content
        root = ET.fromstring(my_xml)
        tracks = []
        for child in root:
            for subchild in child:
                tracks.append(subchild.attrib)
        return tracks
