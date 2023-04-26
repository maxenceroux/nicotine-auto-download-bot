from fastapi import FastAPI
import socket
import json
import time
import os
from discord import SyncWebhook

app = FastAPI()


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
