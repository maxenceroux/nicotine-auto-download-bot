import requests
from requests.auth import HTTPBasicAuth
import hashlib
import xml.etree.ElementTree as ET


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
        for child in root:
            for subchild in child:
                playlist_tracks.append(subchild.attrib["path"])
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
                    if (
                        sub.attrib["name"].lower().strip()
                        == artist_name.lower().strip()
                    ):
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
                albums.append(subchild)
                return albums
        return albums
