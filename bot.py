import os
import asyncio
import yt_dlp

from pyrogram import Client, filters
from pytgcalls import PyTgCalls


# =========================
# RAILWAY VARIABLES
# =========================

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]


# =========================
# TELEGRAM BOT
# =========================

app = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

calls = PyTgCalls(app)


# =========================
# YOUTUBE DOWNLOADER
# =========================

async def get_song(query):

    if not query.startswith("http"):
        query = "ytsearch1:" + query

    # Beberapa client dicoba karena YouTube
    # dapat memblokir salah satu client.
    clients = [
        "tv",
        "web_safari",
        "android_vr",
        "web_embedded"
    ]

    last_error = None

    for client in clients:

        try:

            ydl_opts = {
                "format": "bestaudio/best",

                "outtmpl": "/tmp/%(id)s.%(ext)s",

                "noplaylist": True,

                "quiet": True,

                "no_warnings": True,

                "geo_bypass": True,

                "extractor_args": {
                    "youtube": {
                        "player_client": [client]
                    }
                },

                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192"
                    }
                ]
            }

            loop = asyncio.get_running_loop()

            def download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(query, download=True)

                    if "entries" in info:
                        info = info["entries"][0]

                    return ydl.prepare_filename(info)

            file_path = await loop.run_in_executor(
                None,
                download
            )

            # Setelah postprocessor, ekstensi biasanya menjadi mp3
            base = os.path.splitext(file_path)[0]
            mp3_file = base + ".mp3"

            if os.path.exists(mp3_file):
                return mp3_file

            if os.path.exists(file_path):
                return file_path

        except Exception as e:

            last_error = str(e)

            continue

    raise Exception(
        "YouTube menolak semua client yang dicoba.\n\n"
        + str(last_error)
    )


# =========================
# START
# =========================

@app.on_message(filters.command("start"))
async def start(client, message):

    await message.reply_text(
        "🎵 Music Bot aktif!\n\n"
        "Gunakan:\n"
        "/play judul lagu\n"
        "/pause\n"
        "/resume\n"
        "/stop"
    )


# =========================
# PLAY
# =========================

@app.on_message(filters.command("play"))
async def play_music(client, message):

    if len(message.command) < 2:

        await message.reply_text(
            "❗ Contoh:\n"
            "/play Sheila On 7 - Dan"
        )

        return

    query = " ".join(message.command[1:])

    status = await message.reply_text(
        "🔎 Mencari lagu..."
    )

    try:

        file_path = await get_song(query)

        await status.edit_text(
            "🎵 Memutar lagu..."
        )

        await calls.play(
            message.chat.id,
            file_path
        )

        await status.edit_text(
            "▶️ Sedang memutar:\n"
            f"🎵 {query}"
        )

    except Exception as e:

        await status.edit_text(
            "❌ Gagal memutar lagu.\n\n"
            f"Error:\n{str(e)}"
        )


# =========================
# PAUSE
# =========================

@app.on_message(filters.command("pause"))
async def pause_music(client, message):

    try:

        await calls.pause(
            message.chat.id
        )

        await message.reply_text(
            "⏸️ Lagu dijeda."
        )

    except Exception as e:

        await message.reply_text(
            f"❌ Gagal pause:\n{e}"
        )


# =========================
# RESUME
# =========================

@app.on_message(filters.command("resume"))
async def resume_music(client, message):

    try:

        await calls.resume(
            message.chat.id
        )

        await message.reply_text(
            "▶️ Lagu dilanjutkan."
        )

    except Exception as e:

        await message.reply_text(
            f"❌ Gagal resume:\n{e}"
        )


# =========================
# STOP
# =========================

@app.on_message(filters.command("stop"))
async def stop_music(client, message):

    try:

        await calls.leave_call(
            message.chat.id
        )

        await message.reply_text(
            "⏹️ Musik dihentikan."
        )

    except Exception as e:

        await message.reply_text(
            f"❌ Gagal menghentikan musik:\n{e}"
        )


# =========================
# RUN BOT
# =========================

print("🎵 Music Bot sedang dijalankan...")

calls.run()
