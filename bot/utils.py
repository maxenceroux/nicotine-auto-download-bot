import requests
from bs4 import BeautifulSoup
from clients.spotify_client import SpotifyController
import os
from clients.subsconic_client import SubsonicClient
from unidecode import unidecode
from clients.db_client import DBClient, RaxdioDB
import time
from datetime import datetime


def call_auto_download(album_info: dict):
    url = "http://web:8000/auto_download"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    response = requests.post(url, params=album_info, headers=headers)
    return response


def get_playlist_info(message, is_url=True):
    if is_url:
        playlist_id = message.split("/")[-1].split("?")[0]
    else:
        playlist_id = message
    sp_client = SpotifyController(
        os.environ["SPOTIFY_CLIENT_ID"],
        os.environ["SPOTIFY_CLIENT_SECRET"],
    )
    token = sp_client.get_unauth_token()
    playlist = sp_client.get_playlist_tracks(token, playlist_id)
    unique_albums_ids = []
    for track in playlist:
        album_id = track["album_id"]
        if album_id not in unique_albums_ids:
            unique_albums_ids.append(album_id)
    albums_info = []
    for id in unique_albums_ids:
        albums_info.append(get_spotify_info(id, False))
    return albums_info


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


def create_playlist_file_from_navidrome_playlist(
    playlist_name: str,
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
        with open(f"/playlists/{playlist_name}.m3u", "w+") as f:
            f.write("#EXTM3U\n")
            for playlist in playlist_tracks:
                f.write(f"{music_directory}/{playlist}\n")

        return {
            "message": f"playlist created here: {os.environ['PLAYLIST_DIR']}/{playlist_name}.m3u"
        }
    except Exception as e:
        raise e


def workflow_spotify_playlist(
    playlist_id: str, show_name: str, show_author: str, show_slot: datetime
):
    albums_info = get_playlist_info(playlist_id, is_url=False)
    sp_client = SpotifyController(
        os.environ["SPOTIFY_CLIENT_ID"], os.environ["SPOTIFY_CLIENT_SECRET"]
    )
    token = sp_client.get_unauth_token()
    playlist_tracks = sp_client.get_playlist_tracks(token, playlist_id)
    with DBClient("/db/music.db") as db_client:
        for album in albums_info:
            if not db_client.album_exists(album["album_name"]):
                call_auto_download(album)
    print("Finished searching tracks - Waiting for download")
    time.sleep(45)
    print("Downloads finished - Scanning library")
    subsonic_client = SubsonicClient(
        user=os.environ["NAVIDROME_USER"],
        password=os.environ["NAVIDROME_PWD"],
        salt=os.environ["NAVIDROME_SALT"],
        host=os.environ["NAVIDROME_HOST"],
        port=os.environ["NAVIDROME_PORT"],
        api_version=os.environ["SUBSONIC_API"],
    )
    subsonic_client.start_scan()
    time.sleep(45)
    tracks_path = []
    print("Scan finished - Creating playlist")
    show_time_str = show_slot.strftime("%Y%m%d%H")
    with DBClient("/db/music.db") as db_client:
        for playlist_track in playlist_tracks:
            print(playlist_track["track_name"])
            track_path = db_client.get_medial_file_path_by_title(
                playlist_track["track_name"]
            )
            if track_path:
                tracks_path.append(track_path)
    try:
        playlist_path = (
            f"/playlists/{show_time_str}_{show_name}_{show_author}.m3u"
        )
        with open(playlist_path, "w+") as f:
            f.write("#EXTM3U\n")
            for track in tracks_path:
                f.write(f"{os.environ['BASE_PATH']}{track}\n")
        print("Playlist created successfully")
        with RaxdioDB(os.environ["PG_DB_URL"]) as db:
            db.set_show_playlist_path(show_slot, playlist_path)
    except:
        return {"message": "unsuccessful playlist file creation"}


def create_playlist_file_from_spotify_playlist(
    message: str,
    music_directory: str,
    is_url: bool = True,
):
    if is_url:
        playlist_id = message.split("/")[-1].split("?")[0]
        print(playlist_id)
    else:
        playlist_id = message
    sp_client = SpotifyController(
        os.environ["SPOTIFY_CLIENT_ID"], os.environ["SPOTIFY_CLIENT_SECRET"]
    )
    token = sp_client.get_unauth_token()
    try:
        playlist_info = sp_client.get_playlist_info(token, playlist_id)
        playlist_tracks = sp_client.get_playlist_tracks(token, playlist_id)
    except Exception as e:
        print(e)
        raise
    tracks_path = []
    with DBClient("/db/music.db") as db_client:
        for playlist_track in playlist_tracks:
            track_path = db_client.get_medial_file_path_by_title(
                playlist_track["track_name"]
            )
            if track_path:
                tracks_path.append(track_path)
    try:
        with open(f"/playlists/{playlist_info['name']}.m3u", "w+") as f:
            f.write("#EXTM3U\n")
            for track in tracks_path:
                f.write(f"{music_directory}/{track}\n")
    except:
        return {"message": "unsuccessful playlist file creation"}
    return {
        "message": f"playlist created here: {os.environ['PLAYLIST_DIR']}/{playlist_info['name']}.m3u"
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
        print(album)
        if unidecode(album_name.lower().strip()) in unidecode(
            album["name"].lower().strip()
        ):
            return True
    return False


def get_track_path(album_name: str, artist_name: str, track_name: str):
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
        return None
    albums = subsonic_client.get_artist_albums(artist_id)
    if not albums:
        return None
    this_album = None
    for album in albums:
        if unidecode(album_name.lower().strip()) in unidecode(
            album["name"].lower().strip()
        ):
            this_album = album
            break
    if not this_album:
        return None
    tracks = subsonic_client.get_album_tracks(this_album["id"])
    target_track = unidecode(track_name.lower().strip())
    most_similar_track = ""
    min_distance = float("inf")
    with DBClient("/db/music.db") as db_client:
        for track in tracks:
            this_track = unidecode(track["title"].lower().strip())
            if target_track in this_track:
                file_path = db_client.get_media_file_path(track["id"])
                file_path = file_path.split("/music/")[1]
                return file_path
            distance = levenshtein_distance(target_track, this_track)
            if distance < min_distance:
                most_similar_track = track
                min_distance = distance
        file_path = db_client.get_media_file_path(most_similar_track["id"])
        print(file_path)
        file_path = file_path.split("/music/")[1]
    return file_path


def levenshtein_distance(s1, s2):
    m = len(s1)
    n = len(s2)
    # create a matrix of size (m+1)x(n+1) to store the distances
    d = [[0] * (n + 1) for i in range(m + 1)]
    # initialize the first row and column of the matrix
    for i in range(m + 1):
        d[i][0] = i
    for j in range(n + 1):
        d[0][j] = j
    # fill in the rest of the matrix
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            d[i][j] = min(
                d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost
            )
    # return the distance between s1 and s2
    return d[m][n]
