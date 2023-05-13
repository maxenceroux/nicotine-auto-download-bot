from typing import List, Optional
from fastapi import FastAPI, BackgroundTasks, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import socket
import json
import time
import os
from discord import SyncWebhook
from clients.icecast_client import IcecastClient
from clients.lastfm_client import LastFMClient
from clients.spotify_client import SpotifyController
from clients.db_client import RaxdioDB, DBClient
from utils import (
    get_playlist_info,
    album_already_exists,
    call_auto_download,
    workflow_spotify_playlist,
)
import shutil
import random

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:3004",
    "http://localhost:3005",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from pydantic import BaseModel


class Message(BaseModel):
    username: str
    content: str


class Slot(BaseModel):
    start_datetime: str
    author: str
    name: str
    playlist_url: str
    description: str
    ig_url: Optional[str]
    bc_url: Optional[str]
    sc_url: Optional[str]


class Track(BaseModel):
    index: Optional[int]
    title: str
    artist: Optional[str]


class Playlist(BaseModel):
    start_datetime: str
    author: str
    name: str
    ordered_tracks: List[Track]


@app.post("/daily_shows")
def create_daily_shows():
    with RaxdioDB(os.environ["PG_DB_URL"]) as db:
        shows = db.get_daily_shows()
    playlist_slots = [
        "06",
        "07",
        "08",
        "09",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "20",
        "21",
        "22",
        "23",
        "00",
    ]
    for slot in playlist_slots:
        is_found = False
        for show in shows:
            hour_str = show.start_time.strftime("%H")
            if hour_str == slot:
                old_playlist_path = show.playlist_path
                daily_playlist_path = f"/playlists/{hour_str}.m3u"
                shutil.copy(old_playlist_path, daily_playlist_path)
                is_found = True
        if not is_found:
            src_playlist = "/playlists/raxdio.m3u"
            dest_playlist = f"/playlists/{slot}.m3u"
            with open(src_playlist, "r") as f:
                lines = f.readlines()
            header = lines[0]
            tracks = lines[1:]
            random.shuffle(tracks)
            with open(dest_playlist, "w") as f:
                f.write(header)
                f.writelines(tracks)

    return shows


@app.get("/current_show")
def get_current_show():
    with RaxdioDB(os.environ["PG_DB_URL"]) as db:
        show = db.get_current_show()
    if show:
        return f"{os.environ['PLAYLIST_DIR']}{show.playlist_path}"
    return f"{os.environ['PLAYLIST_DIR']}/playlists/raxdio.m3u"


@app.post("/show")
def create_show(slot: Slot, background_tasks: BackgroundTasks):
    slot_date = datetime.strptime(slot.start_datetime, "%Y-%m-%dT%H:%M:%S.%fZ")
    with RaxdioDB(os.environ["PG_DB_URL"]) as db:
        show = db.create_show(
            slot_date,
            slot.author,
            slot.name,
            slot.playlist_url,
            slot.description,
            slot.ig_url,
            slot.bc_url,
            slot.sc_url,
        )
    playlist_id = slot.playlist_url.split("/")[-1].split("?")[0]
    background_tasks.add_task(
        workflow_spotify_playlist,
        playlist_id,
        slot.name,
        slot.author,
        slot_date,
        slot.description,
    )
    webhook = SyncWebhook.from_url(os.environ["DISCORD_WEBHOOK_URL"])
    webhook.send(
        f"{slot.author} created a show with name {slot.name} on {slot.start_datetime}"
    )
    return {"message": "Data submitted for processing."}


@app.post("/upload_track/")
async def create_upload_track(file: UploadFile = File(...)):
    file_path = os.path.join("/music", file.filename)
    with open(file_path, "wb") as f:
        while True:
            content = await file.read(1024)  # read in 1kb chunk
            if not content:
                break
            f.write(content)
    return {"filename": file.filename}


@app.post("/save_playlist")
def save_playlist(playlist: Playlist):
    show_date = datetime.strptime(
        playlist.start_datetime, "%Y-%m-%dT%H:%M:%S.%fZ"
    )
    show_date_str = show_date.strftime("%Y%m%d%H")
    playlist_path = (
        f"/playlists/{show_date_str}_{playlist.name}_{playlist.author}.m3u"
    )
    with open(playlist_path, "w+") as f:
        f.write("#EXTM3U\n")
        with DBClient("/db/music.db") as db_client:
            for track in playlist.ordered_tracks:
                if track.artist:
                    track_path = db_client.get_medial_file_path_by_title(
                        track.title
                    )
                    f.write(
                        f"{os.environ['BASE_PATH']}{track_path.split('/music')[1]}\n"
                    )
                else:
                    f.write(f"{os.environ['BASE_PATH']}/music/{track.title}\n")
    if show_date.date() == datetime.now().date():
        hour_str = show_date.strftime("%H")
        hour_playlist_path = f"/playlists/{hour_str}.m3u"
        try:
            shutil.copy(playlist_path, hour_playlist_path)
            print(
                f"Playlist copy created successfully with name {hour_playlist_path}"
            )
        except:
            return {"message": "unsuccessful playlist copy creation"}


@app.get("/playlist_tracks")
def get_playlist_tracks(show_time: str, show_name: str, show_author: str):
    show_date = datetime.strptime(show_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    show_date_str = show_date.strftime("%Y%m%d%H")
    playlist_path = f"/playlists/{show_date_str}_{show_name}_{show_author}.m3u"
    if not os.path.exists(playlist_path):
        return None
    tracks = []
    with open(playlist_path, "r") as f:
        next(f)
        with DBClient("/db/music.db") as db_client:
            index = 1
            for track in f:
                path = track.split(os.environ["BASE_PATH"])[-1].strip()
                path = f"/music{path}"
                track_info = db_client.get_track_info_by_path(path)
                tracks.append(
                    {
                        "index": index,
                        "title": track_info[0],
                        "artist": track_info[1],
                    }
                )
                index += 1
    return tracks


@app.get("/shows")
def get_shows():
    with RaxdioDB(os.environ["PG_DB_URL"]) as db:
        shows = db.get_shows()
    return shows


@app.post("/auto_download")
def perform_auto_download(artist_name: str, album_name: str, tracks_cnt: int):
    print("PERFORMING SEARCH")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(
            (os.environ["NICOTINE_HOST"], int(os.environ["NICOTINE_PORT"]))
        )
        search_term = f"{artist_name} {album_name}"
        msg = {"function": "auto_search", "search_term": search_term}
        json_message = json.dumps(msg)
        s.sendall(json_message.encode("utf-8"))
    print("WAITING FOR RESULTS")
    time.sleep(8)
    print("DOWNLOADING")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(
            (os.environ["NICOTINE_HOST"], int(os.environ["NICOTINE_PORT"]))
        )
        msg = {"function": "auto_download", "tracks_cnt": tracks_cnt}
        json_message = json.dumps(msg)
        s.sendall(json_message.encode("utf-8"))
    print("CALLS COMPLETE")
    return {"message": "download should start"}


@app.post("/download_playlist")
async def perform_auto_download(
    playlist_id: str, background_tasks: BackgroundTasks
):
    background_tasks.add_task(workflow_spotify_playlist, playlist_id)
    return {"message": "Data submitted for processing."}


@app.post("/status_message")
def post_status_message(search_term: str, status: str):
    webhook = SyncWebhook.from_url(os.environ["DISCORD_WEBHOOK_URL"])
    if status == "not_found":
        webhook.send(f"{search_term} album search led to 0 results")
    if status == "criterias_not_met":
        webhook.send(
            f"{search_term} album search led to results, but none of the results met set criterias (320 mp3 files)"
        )
    if status == "success":
        webhook.send(f"{search_term} album should now be downloading")
    return True


@app.get("/currently_playing")
def get_currently_playing():
    icecast_client = IcecastClient(
        os.environ["ICECAST_HOST"],
        os.environ["ICECAST_PORT"],
        os.environ["ICECAST_USERNAME"],
        os.environ["ICECAST_PASSWORD"],
    )
    track = icecast_client.get_currently_playing()
    result = {}
    last_fm_client = LastFMClient(os.environ["LAST_FM_API_KEY"])
    try:
        artist = last_fm_client.get_artist_info(track["artist"])
        result["content"] = artist["bio"]["content"].split(
            "User-contributed text"
        )[0]
    except:
        result["content"] = None

    sp_client = SpotifyController(
        os.environ["SPOTIFY_CLIENT_ID"],
        os.environ["SPOTIFY_CLIENT_SECRET"],
    )
    token = sp_client.get_unauth_token()
    track_info = sp_client.search_track_info(
        token, track["title"], track["artist"]
    )

    result["artist_name"] = track["artist"]
    try:
        result["image_url"] = track_info["album"]["images"][0]["url"]
    except:
        result["image_url"] = None
    result["track_name"] = track["title"]
    tracks = []
    with RaxdioDB(os.environ["PG_DB_URL"]) as db:
        if db.is_new_song(result["track_name"], result["artist_name"]):
            db.add_to_history_songs(
                result["track_name"],
                result["artist_name"],
                result["content"],
                result["image_url"],
            )
        all_tracks = db.get_tracks()
        tracks.append(all_tracks[0])
        try:
            tracks.append(all_tracks[1])
        except:
            tracks.append(None)
            tracks.append(None)
            return tracks
        try:
            tracks.append(all_tracks[2])
        except:
            tracks.append(None)
    return tracks


@app.post("/user")
def create_user(username: str):
    with RaxdioDB(os.environ["PG_DB_URL"]) as db:
        db_user = db.insert_user(username)
    return db_user


@app.post("/message")
def create_message(message: Message):
    with RaxdioDB(os.environ["PG_DB_URL"]) as db:
        db.insert_message(message.username, message.content)
    return {"success": "message saved in db"}


@app.get("/messages")
def get_messages():
    with RaxdioDB(os.environ["PG_DB_URL"]) as db:
        messages = db.get_messages()
    return messages
