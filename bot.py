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
# BOT ACCOUNT
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
# DOWNLOAD / SEARCH SONG
# =========================

async def get_song(query):

    if query.startswith("http"):
        source = query
    else:
        source = "scsearch1:" + query

    options = {
        "format": "bestaudio/best",
        "outtmpl": "/tmp/%(id)s.%(ext)s",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
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
# START COMMAND
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
# PLAY COMMAND
# =========================

@bot.on_message(filters.command("play"))
async def play_command(client, message):

    if len(message.command) < 2:

        await message.reply_text(
            "❗ Masukkan judul lagu.\n\n"
            "Contoh:\n"
            "/play Sheila On 7 - Dan"
        )

        return

    query = " ".join(message.command[1:])

    status = await message.reply_text(
        "🔎 Mencari lagu..."
    )

    try:

        # =========================
        # DOWNLOAD
        # =========================

        file_path = await get_song(query)

        await status.edit_text(
            "🎵 Lagu ditemukan.\n"
            "🔊 Menghubungkan ke voice chat..."
        )

        # =========================
        # PLAY
        # =========================

        await calls.play(
            message.chat.id,
            file_path
        )

        await status.edit_text(
            "▶️ Sedang memutar:\n\n"
            f"🎵 {query}"
        )

    except Exception as e:

        await status.edit_text(
            "❌ Gagal memutar lagu.\n\n"
            f"Error:\n{e}"
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
            f"❌ Gagal pause:\n{e}"
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
            f"❌ Gagal resume:\n{e}"
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
            f"❌ Gagal stop:\n{e}"
        )


# =========================
# MAIN
# =========================

async def main():

    print("================================")
    print("🤖 STARTING MUSIC BOT")
    print("================================")

    try:

        # =========================
        # START BOT ACCOUNT
        # =========================

        await bot.start()

        print("✅ BOT ACCOUNT AKTIF")

        # =========================
        # START USER ACCOUNT
        # =========================

        await user.start()

        print("✅ USER ACCOUNT AKTIF")

        # =========================
        # START PYTGCALLS
        # =========================

        await calls.start()

        print("✅ PYTGCALLS AKTIF")
        print("================================")
        print("🎵 MUSIC BOT SIAP")
        print("================================")

        # =========================
        # KEEP ALIVE
        # =========================

        await idle()

    finally:

        print("🛑 Mematikan service...")

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

        print("✅ Semua service berhenti.")


# =========================
# RUN
# =========================

if __name__ == "__main__":
    asyncio.run(main())

Yang saya ubah

Bagian pentingnya sekarang:

await bot.start()
await user.start()
await calls.start()

Jadi urutannya:

Bot → akun user → PyTgCalls → baru "/play"

Itu penting karena "calls" menggunakan akun MTProto "user", dan metode "play()" membutuhkan PyTgCalls yang sudah berjalan. Dokumentasi/contoh PyTgCalls juga menempatkan "start()" sebelum "play()".

⚠️ Satu hal penting

Saya juga mengubah:

calls.start()

menjadi:

await calls.start()

pada versi PyTgCalls yang API-nya async. Source PyTgCalls terbaru mendefinisikan "start()" sebagai coroutine async.

Setelah mengganti "bot.py", Deploy ulang Render, lalu lihat log. Yang kita harapkan muncul:

🤖 STARTING MUSIC BOT
✅ BOT ACCOUNT AKTIF
✅ USER ACCOUNT AKTIF
✅ PYTGCALLS AKTIF
🎵 MUSIC BOT SIAP

Setelah itu masuk ke voice chat grup, lalu coba:

/play Sheila On 7 - Dan

Kalau setelah ini muncul error baru seperti "NoActiveGroupCall", itu masalah yang berbeda—berarti startup sudah benar tetapi voice chat/grupnya belum aktif. PyTgCalls memang membedakan proses start dengan keberadaan group call.
