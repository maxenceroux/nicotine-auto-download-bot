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
        url = f"{self._base_url}/v1/albums/{album_id}"
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

    def get_playlist_info(self, token: str, playlist_id: str):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 401:
                token = self.get_unauth_token()
                return self.get_playlist_info(token, playlist_id)
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            if response.json().get("error"):
                print(response.json().get("error"))
                return {"message": "ID corresponding to no playlist"}
        artists = []
        if response.json().get("next"):
            while response.json().get("next"):
                response = requests.get(url, headers=headers)
                if response.json().get("items"):
                    for item in response.json().get("items"):
                        if item and item.get("track"):
                            if item.get("track").get("artists")[0]:
                                single_artist = {
                                    "playlist_id": playlist_id,
                                    "artist_id": item.get("track").get(
                                        "artists"
                                    )[0]["id"],
                                    "name": item.get("track").get("artists")[0][
                                        "name"
                                    ],
                                    "track_id": item.get("track").get("id"),
                                    "track_name": item.get("track").get("name"),
                                    "album_id": item.get("track")
                                    .get("album")
                                    .get("id"),
                                    "album_name": item.get("track")
                                    .get("album")
                                    .get("name"),
                                }
                                artists.append(single_artist)

                    url = response.json().get("next")
        else:
            for item in response.json().get("items"):
                if item and item.get("track"):
                    if item.get("track").get("artists")[0]:
                        single_artist = {
                            "playlist_id": playlist_id,
                            "artist_id": item.get("track").get("artists")[0][
                                "id"
                            ],
                            "name": item.get("track").get("artists")[0]["name"],
                            "track_id": item.get("track").get("id"),
                            "track_name": item.get("track").get("name"),
                            "album_id": item.get("track")
                            .get("album")
                            .get("id"),
                            "album_name": item.get("track")
                            .get("album")
                            .get("name"),
                        }
                        artists.append(single_artist)
        return artists
