import os
import asyncio
import yt_dlp

from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls


# =========================
# ENVIRONMENT VARIABLES
# =========================

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
SESSION_STRING = os.environ["SESSION_STRING"]


# =========================
# BOT
# =========================

bot = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


# =========================
# USER ACCOUNT
# =========================

user = Client(
    "music_user",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)


# =========================
# PYTGCALLS
# =========================

calls = PyTgCalls(user)


# =========================
# DOWNLOAD LAGU
# =========================

async def get_song(query):

    if query.startswith("http://") or query.startswith("https://"):
        source = query
    else:
        source = "scsearch1:" + query

    options = {
        "format": "bestaudio/best",
        "outtmpl": "/tmp/%(id)s.%(ext)s",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True
    }

    loop = asyncio.get_running_loop()

    def download_song():

        with yt_dlp.YoutubeDL(options) as ydl:

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
        download_song
    )

    if not os.path.exists(filename):
        raise Exception("File lagu tidak ditemukan.")

    return filename


# =========================
# START
# =========================

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


# =========================
# PLAY
# =========================

@bot.on_message(filters.command("play"))
async def play_command(client, message):

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

        file_path = await get_song(query)

        await status.edit_text(
            "🎵 Lagu ditemukan.\n"
            "🔊 Memulai pemutaran..."
        )

        await calls.play(
            message.chat.id,
            file_path
        )

        await status.edit_text(
            "▶️ Sedang memutar:\n\n"
            "🎵 " + query
        )

    except Exception as e:

        await status.edit_text(
            "❌ Gagal memutar lagu.\n\n"
            "Error:\n" + str(e)
        )


# =========================
# PAUSE
# =========================

@bot.on_message(filters.command("pause"))
async def pause_command(client, message):

    try:

        await calls.pause(
            message.chat.id
        )

        await message.reply_text(
            "⏸️ Lagu dijeda."
        )

    except Exception as e:

        await message.reply_text(
            "❌ Gagal pause.\n\n"
            "Error:\n" + str(e)
        )


# =========================
# RESUME
# =========================

@bot.on_message(filters.command("resume"))
async def resume_command(client, message):

    try:

        await calls.resume(
            message.chat.id
        )

        await message.reply_text(
            "▶️ Lagu dilanjutkan."
        )

    except Exception as e:

        await message.reply_text(
            "❌ Gagal resume.\n\n"
            "Error:\n" + str(e)
        )


# =========================
# STOP
# =========================

@bot.on_message(filters.command("stop"))
async def stop_command(client, message):

    try:

        await calls.leave_call(
            message.chat.id
        )

        await message.reply_text(
            "⏹️ Musik dihentikan."
        )

    except Exception as e:

        await message.reply_text(
            "❌ Gagal menghentikan musik.\n\n"
            "Error:\n" + str(e)
        )


# =========================
# MAIN
# =========================

async def main():

    print("================================")
    print("STARTING MUSIC BOT")
    print("================================")

    try:

        print("Starting bot account...")
        await bot.start()
        print("BOT ACCOUNT AKTIF")

        print("Starting user account...")
        await user.start()
        print("USER ACCOUNT AKTIF")

        print("Starting PyTgCalls...")
        await calls.start()
        print("PYTGCALLS AKTIF")

        print("================================")
        print("MUSIC BOT SIAP")
        print("================================")

        await idle()

    except Exception as e:

        print("================================")
        print("ERROR")
        print(str(e))
        print("================================")

    finally:

        print("Stopping services...")

        try:
            await calls.stop()
        except Exception:
            pass

        try:
            await user.stop()
        except Exception:
            pass

        try:
            await bot.stop()
        except Exception:
            pass

        print("SERVICE BERHENTI")


# =========================
# RUN
# =========================

if __name__ == "__main__":
    asyncio.run(main())
