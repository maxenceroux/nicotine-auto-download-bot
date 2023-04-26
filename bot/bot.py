import discord
import os
from utils import *

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
        playlist_id = get_navidrome_playlist_id(message.content)
        if playlist_id:
            create_navidrome_playlist_file(playlist_id)
            await message.channel.send(
                f"Playlist file created from {message.content} playlist"
            )
        else:
            await message.channel.send("Playlist not found")
            return False


client.run(os.environ["DISCORD_TOKEN"])
