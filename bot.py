import os
import asyncio
import yt_dlp

from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

app = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

calls = PyTgCalls(app)


async def get_song(query):
    options = {
        "format": "bestaudio/best",
        "outtmpl": "song.%(ext)s",
        "noplaylist": True,
        "quiet": True,
    }

    def download():
        with yt_dlp.YoutubeDL(options) as ydl:
            if not query.startswith(("http://", "https://")):
                query = f"ytsearch1:{query}"

            info = ydl.extract_info(query, download=True)

            if "entries" in info:
                info = info["entries"][0]

            return ydl.prepare_filename(info), info["title"]

    return await asyncio.to_thread(download)


@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "🎵 Music Bot aktif!\n\n"
        "/play judul lagu\n"
        "/stop\n"
        "/pause\n"
        "/resume"
    )


@app.on_message(filters.command("play"))
async def play(client, message):

    if len(message.command) < 2:
        await message.reply_text(
            "Contoh:\n/play Dewa 19 Kangen"
        )
        return

    query = message.text.split(None, 1)[1]

    msg = await message.reply_text("🔎 Mencari lagu...")

    try:
        file_path, title = await get_song(query)

        await msg.edit_text(
            f"🎵 {title}\n🔊 Memulai pemutaran..."
        )

        await calls.play(
            message.chat.id,
            Media
