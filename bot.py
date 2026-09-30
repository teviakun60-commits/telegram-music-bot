import os
import asyncio
import yt_dlp

from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream


API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
SESSION_STRING = os.environ["SESSION_STRING"]


bot = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


user = Client(
    "music_user",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)


calls = PyTgCalls(user)


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
        "no_warnings": True
    }

    loop = asyncio.get_running_loop()

    def download():
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(source, download=True)

            if "entries" in info:
                info = info["entries"][0]

            return ydl.prepare_filename(info)

    filename = await loop.run_in_executor(None, download)

    if not os.path.exists(filename):
        raise Exception("File lagu tidak ditemukan.")

    return filename


@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "🎵 MUSIC BOT AKTIF!\n\n"
        "/play judul lagu\n"
        "/pause\n"
        "/resume\n"
        "/stop"
    )


@bot.on_message(filters.command("play"))
async def play(client, message):
    if len(message.command) < 2:
        await message.reply_text(
            "Contoh:\n/play Sheila On 7 - Dan"
        )
        return

    query = " ".join(message.command[1:])
    msg = await message.reply_text("🔎 Mencari lagu...")

    try:
        file_path = await get_song(query)

        await msg.edit_text(
            "🎵 Lagu ditemukan.\n"
            "🔊 Masuk ke voice chat..."
        )

        await calls.play(
            message.chat.id,
            MediaStream(file_path)
        )

        await msg.edit_text(
            f"▶️ Sedang memutar:\n🎵 {query}"
        )

    except Exception as e:
        await msg.edit_text(
            f"❌ Gagal memutar lagu.\n\n{e}"
        )


@bot.on_message(filters.command("pause"))
async def pause(client, message):
    try:
        await calls.pause(message.chat.id)
        await message.reply_text("⏸️ Lagu dijeda.")
    except Exception as e:
        await message.reply_text(f"❌ {e}")


@bot.on_message(filters.command("resume"))
async def resume(client, message):
    try:
        await calls.resume(message.chat.id)
        await message.reply_text("▶️ Lagu dilanjutkan.")
    except Exception as e:
        await message.reply_text(f"❌ {e}")


@bot.on_message(filters.command("stop"))
async def stop(client, message):
    try:
        await calls.leave_call(message.chat.id)
        await message.reply_text("⏹️ Musik dihentikan.")
    except Exception as e:
        await message.reply_text(f"❌ {e}")


async def main():
    print("🤖 Starting bot...")

    await bot.start()

    print("✅ Bot account aktif")

    calls.start()

    print("✅ User account aktif")
    print("🎵 Music bot siap")

    await idle()

    await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
