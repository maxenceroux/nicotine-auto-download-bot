import requests
from bs4 import BeautifulSoup
from spotify_client import SpotifyController
import os
import hashlib
import xml.etree.ElementTree as ET
from subsconic_client import SubsonicClient


def call_auto_download(album_info: dict):
    url = "http://web:8000/auto_download"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    response = requests.post(url, params=album_info, headers=headers)
    return response


def get_bandcamp_info(message):
    response = requests.get(message)
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.text
    album_name = title.split(" | ")[0]
    artist_name = title.split(" | ")[1]
    tracks_cnt = len(soup.find_all(_class="track_row_view"))
    return {
        "artist_name": artist_name,
        "album_name": album_name,
        "tracks_cnt": tracks_cnt,
    }


def get_spotify_info(message, is_url=True):
    if is_url:
        album_id = message.split("/")[-1].split("?")[0]
    else:
        album_id = message
    sp_client = SpotifyController(
        os.environ["SPOTIFY_CLIENT_ID"], os.environ["SPOTIFY_CLIENT_SECRET"]
    )
    token = sp_client.get_unauth_token()
    try:
        album_info = sp_client.get_album_info(token, album_id)
    except:
        raise
    return {
        "artist_name": album_info["artist_name"],
        "album_name": album_info["album_name"],
        "tracks_cnt": album_info["tracks_cnt"],
    }


def get_navidrome_playlist_id(navidrome_playlist_name):
    c = "myapi"
    token = hashlib.md5(
        f'{os.environ["NAVIDROME_PWD"]}{os.environ["NAVIDROME_SALT"]}'.encode()
    ).hexdigest()
    playlist_id = "a1d847d6-48e4-44f6-8339-0efcbd35ff2d"
    params = {
        "u": os.environ["NAVIDROME_USER"],
        "v": os.environ["SUBSONIC_API"],
        "c": c,
        "t": token,
        "s": os.environ["NAVIDROME_SALT"],
        "id": playlist_id,
    }
    url = f'http://{os.environ["NAVIDROME_HOST"]}:{os.environ["NAVIDROME_PORT"]}/rest/getPlaylists'
    response = requests.get(url, params=params)
    my_xml = response.content
    root = ET.fromstring(my_xml)
    for child in root:
        for subchild in child:
            if subchild.attrib["name"] == navidrome_playlist_name:
                return subchild.attrib["id"]
    return False


def create_navidrome_playlist_file(
    playlist_name: str,
    playlist_directory: str,
    music_directory: str,
):
    subsonic_client = SubsonicClient(
        user=os.environ["NAVIDROME_USER"],
        password=os.environ["NAVIDROME_PWD"],
        salt=os.environ["NAVIDROME_SALT"],
        host=os.environ["NAVIDROME_HOST"],
        port=os.environ["NAVIDROME_PORT"],
        api_version=os.environ["SUBSONIC_API"],
    )
    playlist_id = subsonic_client.get_playlist_id(playlist_name=playlist_name)
    playlist_tracks = subsonic_client.get_playlist_tracks(
        playlist_id=playlist_id
    )
    try:
        with open(f"{playlist_directory}/{playlist_name}.m3u", "w+") as f:
            f.write("#EXTM3U\n")
            for playlist in playlist_tracks:
                f.write(f"{music_directory}/{playlist}\n")
    except:
        return {"message": "unsuccessful playlist file creation"}
    return {
        "message": f"playlist created here: {playlist_directory}/{playlist_name}.m3u"
    }


def album_already_exists(album_name: str, artist_name: str):
    subsonic_client = SubsonicClient(
        user=os.environ["NAVIDROME_USER"],
        password=os.environ["NAVIDROME_PWD"],
        salt=os.environ["NAVIDROME_SALT"],
        host=os.environ["NAVIDROME_HOST"],
        port=os.environ["NAVIDROME_PORT"],
        api_version=os.environ["SUBSONIC_API"],
    )
    artist_id = subsonic_client.get_artist_id(artist_name)
    if not artist_id:
        return False
    albums = subsonic_client.get_artist_albums(artist_id)
    if not albums:
        return False
    for album in albums:
        if album_name.lower().strip() in album.attrib["name"].lower().strip():
            return True
    return False
