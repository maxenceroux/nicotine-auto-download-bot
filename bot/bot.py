import discord
import os
from utils import *
import time

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))


@client.event
async def on_message(message):
    if message.author == client.user or message.author.name == "Nicotine+":
        return
    print("New message received: {0.content}".format(message))
    if message.channel.name == "downloads":
        if message.content.startswith("!playlist"):
            if "spotify.com" in message.content:
                albums_info = get_playlist_info(message.content, True)
                for album_info in albums_info:
                    if album_already_exists(
                        album_info["album_name"], album_info["artist_name"]
                    ):
                        print(
                            f'album {album_info["album_name"]} already existing - skipping'
                        )
                    else:
                        call_auto_download(album_info)
                return True
        if "bandcamp.com" in message.content:
            try:
                album_info = get_bandcamp_info(message.content)
            except:
                await message.channel.send("Album not found on Bandcamp")
                return False
        if "spotify.com" in message.content:
            try:
                album_info = get_spotify_info(message.content)
            except:
                await message.channel.send("Album not found on Spotify")
                return False
        else:
            await message.channel.send(
                "Platform not supported yet. Only Spotify and Bandcamp are supported"
            )
            return False
        call_auto_download(album_info)
    if message.channel.name == "playlists":
        if "spotify.com" in message.content:
            try:
                create_playlist_file_from_spotify_playlist(
                    message.content,
                    os.environ["BASE_PATH"],
                    True,
                )
                await message.channel.send(
                    f"Playlist file created from {message.content} playlist"
                )
                return True
            except Exception as e:
                await message.channel.send(f"Playlist not found {e}")
                return False
        try:
            create_playlist_file_from_navidrome_playlist(
                message.content,
                os.environ["BASE_PATH"],
            )
            await message.channel.send(
                f"Playlist file created from {message.content} playlist"
            )
        except Exception as e:
            await message.channel.send(f"Playlist not found {e}")
            return False


client.run(os.environ["DISCORD_TOKEN"])
