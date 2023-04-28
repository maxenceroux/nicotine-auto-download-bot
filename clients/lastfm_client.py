import requests
import json


class LastFMClient:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_track_info(self, track_name, artist_name):
        url = f"http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={self.api_key}&artist={artist_name}&track={track_name}&format=json"
        response = requests.get(url)

        if response.status_code == 200:
            data = json.loads(response.text)
            return data["track"]
        else:
            return None

    def get_artist_info(self, artist_name):
        url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&api_key={self.api_key}&artist={artist_name}&format=json"
        response = requests.get(url)

        if response.status_code == 200:
            data = json.loads(response.text)
            return data["artist"]
        else:
            return None
