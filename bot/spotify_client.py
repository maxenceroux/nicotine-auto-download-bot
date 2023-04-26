import requests
from requests.auth import HTTPBasicAuth
import datetime
import json


class SpotifyController:
    def __init__(
        self, client_id: str = None, client_secret: str = None
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self._base_url = "https://api.spotify.com"

    def get_unauth_token(self) -> str:
        url = "https://accounts.spotify.com/api/token"
        payload = "grant_type=client_credentials"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            response = requests.post(
                url,
                auth=HTTPBasicAuth(
                    self.client_id,
                    self.client_secret,
                ),
                headers=headers,
                data=payload,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        return response.json().get("access_token")

    def get_album_info(self, token: str, album_id: str):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        url = f"https://api.spotify.com/v1/albums/{album_id}"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 401:
                token = self.get_unauth_token()
                return self.get_album_info(token, album_id)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        data = response.json()
        album = {}
        album["album_name"] = data.get("name")
        album["artist_name"] = data.get("artists")[0].get("name")
        album["tracks_cnt"] = data.get("total_tracks")
        return album
