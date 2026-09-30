import os
import asyncio
import shutil
import yt_dlp

from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls


# =========================================================
# CEK FFMPEG / FFPROBE
# =========================================================

print("================================")
print("CHECK FFMPEG / FFPROBE")
print("ffmpeg  :", shutil.which("ffmpeg"))
print("ffprobe :", shutil.which("ffprobe"))
print("================================")


# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
SESSION_STRING = os.environ["SESSION_STRING"]


# =========================================================
# BOT ACCOUNT
# =========================================================

bot = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


# =========================================================
# USER ACCOUNT
# =========================================================

user = Client(
    "music_user",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)


# =========================================================
# PYTGCALLS
# PENTING:
# JANGAN buat PyTgCalls di sini.
# Dibuat di dalam main() agar loop sama.
# =========================================================

calls = None


# =========================================================
# DOWNLOAD LAGU
# =========================================================

async def get_song(query):

    if query.startswith("http://") or query.startswith("https://"):
        source = query
    else:
        source = "scsearch1:" + query

    ffmpeg_path = shutil.which("ffmpeg")

    if not ffmpeg_path:
        raise Exception("ffmpeg tidak ditemukan di Railway.")

    options = {
        "format": "bestaudio/best",

        "outtmpl": "/tmp/%(id)s.%(ext)s",

        "noplaylist": True,

        "quiet": True,

        "no_warnings": True,

        "ffmpeg_location": ffmpeg_path,
    }

    loop = asyncio.get_running_loop()

    def download_song():

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                source,
                download=True
            )

            if "entries" in info:

                if not info["entries"]:
                    raise Exception("Lagu tidak ditemukan.")

                info = info["entries"][0]

            filename = ydl.prepare_filename(info)

            return filename

    filename = await loop.run_in_executor(
        None,
        download_song
    )

    if not os.path.exists(filename):

        raise Exception(
            "File lagu tidak ditemukan setelah download."
        )

    return filename


# =========================================================
# START
# =========================================================

@bot.on_message(filters.command("start"))
async def start_command(client, message):

    await message.reply_text(
        "🎵 MUSIC BOT AKTIF!\n\n"
        "Perintah:\n\n"
        "/play judul lagu\n"
        "/pause\n"
        "/resume\n"
        "/stop"
    )


# =========================================================
# PLAY
# =========================================================

@bot.on_message(filters.command("play"))
async def play_command(client, message):

    global calls

    if calls is None:

        await message.reply_text(
            "❌ Sistem musik belum siap."
        )

        return

    if len(message.command) < 2:

        await message.reply_text(
            "❗ Masukkan judul lagu.\n\n"
            "Contoh:\n"
            "/play Sheila On 7 Dan"
        )

        return

    query = " ".join(message.command[1:])

    status = await message.reply_text(
        "🔎 Mencari lagu..."
    )

    try:

        # =================================================
        # CEK FFMPEG
        # =================================================

        ffmpeg_path = shutil.which("ffmpeg")
        ffprobe_path = shutil.which("ffprobe")

        print("================================")
        print("MEMERIKSA FFMPEG")
        print("ffmpeg :", ffmpeg_path)
        print("ffprobe:", ffprobe_path)
        print("================================")

        if not ffmpeg_path:

            raise Exception(
                "ffmpeg tidak ditemukan di Railway."
            )

        if not ffprobe_path:

            raise Exception(
                "ffprobe tidak ditemukan di Railway."
            )

        # =================================================
        # DOWNLOAD
        # =================================================

        print("Mencari lagu:", query)

        file_path = await get_song(query)

        print("File lagu:", file_path)

        if not os.path.exists(file_path):

            raise Exception(
                "File lagu tidak ditemukan."
            )

        # =================================================
        # UPDATE STATUS
        # =================================================

        await status.edit_text(
            "🎵 Lagu ditemukan.\n"
            "🔊 Memulai pemutaran..."
        )

        # =================================================
        # PLAY
        # =================================================

        print("Memulai pemutaran...")
        print("Chat ID:", message.chat.id)
        print("File:", file_path)

        await calls.play(
            message.chat.id,
            file_path
        )

        print("Lagu berhasil diputar.")

        await status.edit_text(
            "▶️ Sedang memutar:\n\n"
            "🎵 " + query
        )

    except Exception as e:

        print("================================")
        print("ERROR PLAY")
        print(type(e).__name__)
        print(str(e))
        print("================================")

        await status.edit_text(
            "❌ Gagal memutar lagu.\n\n"
            "Error:\n" + str(e)
        )


# =========================================================
# PAUSE
# =========================================================

@bot.on_message(filters.command("pause"))
async def pause_command(client, message):

    global calls

    try:

        if calls is None:
            raise Exception("PyTgCalls belum aktif.")

        await calls.pause(
            message.chat.id
        )

        await message.reply_text(
            "⏸️ Lagu dijeda."
        )

    except Exception as e:

        print("ERROR PAUSE:", e)

        await message.reply_text(
            "❌ Gagal pause.\n\n"
            "Error:\n" + str(e)
        )


# =========================================================
# RESUME
# =========================================================

@bot.on_message(filters.command("resume"))
async def resume_command(client, message):

    global calls

    try:

        if calls is None:
            raise Exception("PyTgCalls belum aktif.")

        await calls.resume(
            message.chat.id
        )

        await message.reply_text(
            "▶️ Lagu dilanjutkan."
        )

    except Exception as e:

        print("ERROR RESUME:", e)

        await message.reply_text(
            "❌ Gagal resume.\n\n"
            "Error:\n" + str(e)
        )


# =========================================================
# STOP
# =========================================================

@bot.on_message(filters.command("stop"))
async def stop_command(client, message):

    global calls

    try:

        if calls is None:
            raise Exception("PyTgCalls belum aktif.")

        await calls.leave_call(
            message.chat.id
        )

        await message.reply_text(
            "⏹️ Musik dihentikan."
        )

    except Exception as e:

        print("ERROR STOP:", e)

        await message.reply_text(
            "❌ Gagal menghentikan musik.\n\n"
            "Error:\n" + str(e)
        )


# =========================================================
# MAIN
# =========================================================

async def main():

    global calls

    print("================================")
    print("STARTING MUSIC BOT")
    print("================================")

    try:

        # =================================================
        # START BOT
        # =================================================

        print("Starting bot account...")

        await bot.start()

        print("BOT ACCOUNT AKTIF")

        # =================================================
        # START USER
        # =================================================

        print("Starting user account...")

        await user.start()

        print("USER ACCOUNT AKTIF")

        # =================================================
        # START PYTGCALLS
        # PENTING:
        # Dibuat DI SINI agar menggunakan event loop
        # yang sama dengan seluruh program.
        # =================================================

        print("Starting PyTgCalls...")

        calls = PyTgCalls(user)

        await calls.start()

        print("PYTGCALLS AKTIF")

        # =================================================
        # CEK FFMPEG SEKALI LAGI
        # =================================================

        print("================================")
        print("SYSTEM CHECK")
        print("ffmpeg  :", shutil.which("ffmpeg"))
        print("ffprobe :", shutil.which("ffprobe"))
        print("================================")

        # =================================================
        # BOT SIAP
        # =================================================

        print("================================")
        print("MUSIC BOT SIAP")
        print("================================")

        await idle()

    except Exception as e:

        print("================================")
        print("MAIN ERROR")
        print(type(e).__name__)
        print(str(e))
        print("================================")

    finally:

        print("Stopping services...")

        if calls is not None:

            try:
                await calls.stop()
            except Exception as e:
                print("CALLS STOP ERROR:", e)

        try:
            await user.stop()
        except Exception as e:
            print("USER STOP ERROR:", e)

        try:
            await bot.stop()
        except Exception as e:
            print("BOT STOP ERROR:", e)

        print("SERVICE BERHENTI")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    asyncio.run(main())
