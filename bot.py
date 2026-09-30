import os
import asyncio
import yt_dlp

from pyrogram import Client, filters
from pytgcalls import PyTgCalls


# =========================
# VARIABLES RAILWAY
# =========================

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]


# =========================
# TELEGRAM
# =========================

app = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

calls = PyTgCalls(app)


# =========================
# CARI & DOWNLOAD SOUNDCloud
# =========================

async def get_song(query):

    # Kalau user memasukkan link SoundCloud,
    # gunakan link tersebut.
    if query.startswith("http"):
        source = query
    else:
        source = "scsearch1:" + query

    ydl_opts = {
        "format": "bestaudio/best",

        "outtmpl": "/tmp/%(id)s.%(ext)s",

        "noplaylist": True,

        "quiet": True,

        "no_warnings": True,

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

            info = ydl.extract_info(
                source,
                download=True
            )

            if "entries" in info:
                info = info["entries"][0]

            filename = ydl.prepare_filename(info)

            return filename

    filename = await loop.run_in_executor(
        None,
        download
    )

    # Setelah FFmpeg mengubah menjadi MP3
    mp3_file = os.path.splitext(filename)[0] + ".mp3"

    if os.path.exists(mp3_file):
        return mp3_file

    if os.path.exists(filename):
        return filename

    raise Exception("File lagu tidak ditemukan.")


# =========================
# START
# =========================

@app.on_message(filters.command("start"))
async def start(client, message):

    await message.reply_text(
        "🎵 MUSIC BOT AKTIF!\n\n"
        "Perintah:\n"
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
        "🔎 Mencari lagu di SoundCloud..."
    )

    try:

        file_path = await get_song(query)

        await status.edit_text(
            "🎵 Lagu ditemukan.\n"
            "▶️ Memulai pemutaran..."
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
            f"❌ Gagal stop:\n{e}"
        )


# =========================
# START BOT
# =========================

print("🎵 Music Bot sedang berjalan...")

calls.run()
