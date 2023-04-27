import requests
from bs4 import BeautifulSoup
from spotify_client import SpotifyController
import os
from subsconic_client import SubsonicClient
from unidecode import unidecode
from db_client import DBClient


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


def create_playlist_file_from_spotify_playlist(
    message: str,
    music_directory: str,
    is_url: bool = True,
):
    if is_url:
        playlist_id = message.split("/")[-1].split("?")[0]
    else:
        playlist_id = message
    sp_client = SpotifyController(
        os.environ["SPOTIFY_CLIENT_ID"], os.environ["SPOTIFY_CLIENT_SECRET"]
    )
    token = sp_client.get_unauth_token()
    try:
        playlist_info = sp_client.get_playlist_info(token, playlist_id)
        playlist_tracks = sp_client.get_playlist_tracks(token, playlist_id)
    except:
        raise

    tracks_path = []
    for playlist_track in playlist_tracks:
        tracks_path.append(
            get_track_path(
                playlist_track["album_name"],
                playlist_track["name"],
                playlist_track["track_name"],
            )
        )
    try:
        with open(f"/playlists/{playlist_info['name']}.m3u", "w+") as f:
            f.write("#EXTM3U\n")
            for playlist in playlist_tracks:
                f.write(f"{music_directory}/{playlist}\n")
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
        if unidecode(album_name.lower().strip()) in unidecode(
            album.attrib["name"].lower().strip()
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
                return db_client.get_media_file_path(track["path"])
            distance = levenshtein_distance(target_track, this_track)
            if distance < min_distance:
                most_similar_track = track
                min_distance = distance
        path = db_client.get_media_file_path(most_similar_track["path"])
    return path


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
