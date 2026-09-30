import os
import asyncio
import yt_dlp

from pyrogram import Client, filters
from pytgcalls import PyTgCalls


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
        search_query = query

        if not search_query.startswith(("http://", "https://")):
            search_query = f"ytsearch1:{search_query}"

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(
                search_query,
                download=True
            )

            if "entries" in info:
                info = info["entries"][0]

            file_path = ydl.prepare_filename(info)
            title = info["title"]

            return file_path, title

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

    msg = await message.reply_text(
        "🔎 Mencari lagu..."
    )

    try:
        file_path, title = await get_song(query)

        await msg.edit_text(
            f"🎵 {title}\n"
            "🔊 Memulai pemutaran..."
        )

        await calls.play(
            message.chat.id,
            file_path
        )

    except Exception as e:
        await msg.edit_text(
            f"❌ Gagal memutar lagu.\n\n"
            f"Error:\n{e}"
        )


@app.on_message(filters.command("pause"))
async def pause(client, message):
    try:
        await calls.pause(message.chat.id)

        await message.reply_text(
            "⏸️ Musik dijeda."
        )

    except Exception as e:
        await message.reply_text(
            f"❌ Gagal pause:\n{e}"
        )


@app.on_message(filters.command("resume"))
async def resume(client, message):
    try:
        await calls.resume(message.chat.id)

        await message.reply_text(
            "▶️ Musik dilanjutkan."
        )

    except Exception as e:
        await message.reply_text(
            f"❌ Gagal resume:\n{e}"
        )


@app.on_message(filters.command("stop"))
async def stop(client, message):
    try:
        await calls.leave_call(message.chat.id)

        await message.reply_text(
            "⏹️ Musik dihentikan."
        )

    except Exception as e:
        await message.reply_text(
            f"❌ Gagal menghentikan musik:\n{e}"
        )


print("🎵 Music Bot aktif...")

calls.run()
