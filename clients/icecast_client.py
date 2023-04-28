import requests
import xml.etree.ElementTree as ET


class IcecastClient:
    def __init__(self, icecast_host, icecast_port, username, password):
        self.username = username
        self.password = password
        self._base_url = f"http://{icecast_host}:{icecast_port}"

    def get_currently_playing(self):
        url = f"{self._base_url}/admin/stats"
        response = requests.get(url, auth=(self.username, self.password))
        root = ET.fromstring(response.content)
        source = root.find("source")
        title = source.find("title").text
        artist = source.find("artist").text
        return {"artist": artist, "title": title}
