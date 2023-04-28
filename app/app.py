from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import socket
import json
import time
import os
from discord import SyncWebhook
from clients.icecast_client import IcecastClient
from clients.lastfm_client import LastFMClient
from clients.spotify_client import SpotifyController

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    last_fm_client = LastFMClient(os.environ["LAST_FM_API_KEY"])
    artist = last_fm_client.get_artist_info(track["artist"])
    sp_client = SpotifyController(
        os.environ["SPOTIFY_CLIENT_ID"],
        os.environ["SPOTIFY_CLIENT_SECRET"],
    )
    token = sp_client.get_unauth_token()
    track_info = sp_client.search_track_info(
        token, track["title"], track["artist"]
    )
    result = {}
    result["artist_name"] = artist["name"]
    try:
        result["image_url"] = track_info["album"]["images"][0]["url"]
    except:
        result["image_url"] = None
    result["content"] = artist["bio"]["content"].split("User-contributed text")[
        0
    ]
    result["track_name"] = track["title"]
    return result
