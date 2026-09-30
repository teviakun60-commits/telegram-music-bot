import os
import asyncio
import shutil
import yt_dlp

from pyrogram import Client, filters, idle
from pytgcalls import PyTgCalls
from pytgcalls import filters as fl
from pytgcalls.types import StreamEnded


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
# =========================================================

calls = None


# =========================================================
# MUSIC QUEUE
#
# queue[chat_id] = [
#     {
#         "title": "...",
#         "file": "..."
#     }
# ]
# =========================================================

music_queue = {}

# Lagu yang sedang diputar
current_song = {}

# Lock supaya pergantian lagu tidak bentrok
queue_locks = {}

# Menandai chat yang sedang melakukan skip/stop
manual_change = set()


# =========================================================
# LOCK PER CHAT
# =========================================================

def get_queue_lock(chat_id):

    if chat_id not in queue_locks:
        queue_locks[chat_id] = asyncio.Lock()

    return queue_locks[chat_id]


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
        raise Exception(
            "ffmpeg tidak ditemukan di Railway."
        )

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
                    raise Exception(
                        "Lagu tidak ditemukan."
                    )

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
# PUTAR LAGU
# =========================================================

async def play_song(
    chat_id,
    title,
    file_path,
    announce=True
):

    global calls

    if calls is None:
        raise Exception(
            "PyTgCalls belum aktif."
        )

    print("================================")
    print("PLAY SONG")
    print("Chat:", chat_id)
    print("Title:", title)
    print("File:", file_path)
    print("================================")

    await calls.play(
        chat_id,
        file_path
    )

    current_song[chat_id] = {
        "title": title,
        "file": file_path
    }

    if announce:

        try:

            await bot.send_message(
                chat_id,
                "▶️ Sedang memutar:\n\n"
                "🎵 " + title
            )

        except Exception as e:

            print(
                "Gagal mengirim status:",
                e
            )


# =========================================================
# PUTAR LAGU BERIKUTNYA
# =========================================================

async def play_next(chat_id):

    lock = get_queue_lock(chat_id)

    async with lock:

        queue = music_queue.get(
            chat_id,
            []
        )

        if not queue:

            print(
                "Antrean kosong:",
                chat_id
            )

            current_song.pop(
                chat_id,
                None
            )

            return False

        next_song = queue.pop(0)

        music_queue[chat_id] = queue

        title = next_song["title"]
        file_path = next_song["file"]

        old_song = current_song.get(
            chat_id
        )

        old_file = None

        if old_song:
            old_file = old_song.get("file")

        try:

            await play_song(
                chat_id,
                title,
                file_path,
                announce=True
            )

            # Hapus file lagu sebelumnya
            if (
                old_file
                and old_file != file_path
                and os.path.exists(old_file)
            ):

                try:
                    os.remove(old_file)
                    print(
                        "File lama dihapus:",
                        old_file
                    )
                except Exception as e:
                    print(
                        "Gagal hapus file lama:",
                        e
                    )

            return True

        except Exception as e:

            print(
                "Gagal memutar lagu berikutnya:",
                e
            )

            # Kalau gagal, coba lagu berikutnya
            if os.path.exists(file_path):

                try:
                    os.remove(file_path)
                except Exception:
                    pass

            if music_queue.get(chat_id):

                return await play_next(
                    chat_id
                )

            return False


# =========================================================
# START
# =========================================================

@bot.on_message(filters.command("start"))
async def start_command(client, message):

    await message.reply_text(
        "🎵 MUSIC BOT AKTIF!\n\n"

        "Perintah:\n\n"

        "/play judul lagu\n"
        "/queue - lihat antrean\n"
        "/skip - lewati lagu\n"
        "/pause - jeda\n"
        "/resume - lanjut\n"
        "/stop - berhenti"
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

    query = " ".join(
        message.command[1:]
    )

    status = await message.reply_text(
        "🔎 Mencari lagu..."
    )

    try:

        # =================================================
        # CEK FFMPEG
        # =================================================

        ffmpeg_path = shutil.which(
            "ffmpeg"
        )

        ffprobe_path = shutil.which(
            "ffprobe"
        )

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

        print(
            "Mencari lagu:",
            query
        )

        file_path = await get_song(
            query
        )

        print(
            "File lagu:",
            file_path
        )

        if not os.path.exists(
            file_path
        ):

            raise Exception(
                "File lagu tidak ditemukan."
            )

        # =================================================
        # CEK APAKAH ADA LAGU SEDANG DIPUTAR
        # =================================================

        chat_id = message.chat.id

        if chat_id in current_song:

            # =================================================
            # MASUKKAN KE ANTREAN
            # =================================================

            if chat_id not in music_queue:

                music_queue[chat_id] = []

            music_queue[chat_id].append(
                {
                    "title": query,
                    "file": file_path
                }
            )

            nomor = len(
                music_queue[chat_id]
            )

            await status.edit_text(
                "➕ Masuk antrean!\n\n"

                f"🎵 {query}\n"
                f"📋 Posisi antrean: {nomor}"
            )

            print(
                "Lagu masuk antrean:",
                query
            )

            return

        # =================================================
        # BELUM ADA LAGU
        # LANGSUNG PUTAR
        # =================================================

        await status.edit_text(
            "🎵 Lagu ditemukan.\n"
            "🔊 Memulai pemutaran..."
        )

        await play_song(
            chat_id,
            query,
            file_path
        )

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
# QUEUE
# =========================================================

@bot.on_message(filters.command("queue"))
async def queue_command(client, message):

    chat_id = message.chat.id

    queue = music_queue.get(
        chat_id,
        []
    )

    current = current_song.get(
        chat_id
    )

    if not current and not queue:

        await message.reply_text(
            "📋 Antrean kosong."
        )

        return

    text = "🎵 MUSIC QUEUE\n\n"

    if current:

        text += (
            "▶️ SEKARANG:\n"
            f"🎵 {current['title']}\n\n"
        )

    if queue:

        text += "📋 ANTREAN:\n\n"

        for i, song in enumerate(
            queue,
            start=1
        ):

            text += (
                f"{i}. "
                f"{song['title']}\n"
            )

    else:

        text += (
            "📋 Tidak ada lagu berikutnya."
        )

    await message.reply_text(
        text
    )


# =========================================================
# SKIP
# =========================================================

@bot.on_message(filters.command("skip"))
async def skip_command(client, message):

    chat_id = message.chat.id

    if chat_id not in current_song:

        await message.reply_text(
            "❌ Tidak ada lagu yang sedang diputar."
        )

        return

    lock = get_queue_lock(
        chat_id
    )

    async with lock:

        old_song = current_song.get(
            chat_id
        )

        old_file = None

        if old_song:

            old_file = old_song.get(
                "file"
            )

        manual_change.add(
            chat_id
        )

        try:

            queue = music_queue.get(
                chat_id,
                []
            )

            if queue:

                next_song = queue.pop(0)

                music_queue[chat_id] = queue

                await play_song(
                    chat_id,
                    next_song["title"],
                    next_song["file"]
                )

                if (
                    old_file
                    and os.path.exists(old_file)
                ):

                    try:
                        os.remove(
                            old_file
                        )
                    except Exception:
                        pass

                await message.reply_text(
                    "⏭️ Lagu dilewati.\n\n"
                    "▶️ Berikutnya:\n"
                    f"🎵 {next_song['title']}"
                )

            else:

                try:

                    await calls.leave_call(
                        chat_id
                    )

                except Exception:
                    pass

                current_song.pop(
                    chat_id,
                    None
                )

                await message.reply_text(
                    "⏭️ Lagu dilewati.\n"
                    "📋 Antrean sudah habis."
                )

                if (
                    old_file
                    and os.path.exists(old_file)
                ):

                    try:
                        os.remove(
                            old_file
                        )
                    except Exception:
                        pass

        finally:

            manual_change.discard(
                chat_id
            )


# =========================================================
# PAUSE
# =========================================================

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


# =========================================================
# RESUME
# =========================================================

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


# =========================================================
# STOP
# =========================================================

@bot.on_message(filters.command("stop"))
async def stop_command(client, message):

    chat_id = message.chat.id

    manual_change.add(
        chat_id
    )

    try:

        # =================================================
        # HAPUS FILE LAGU YANG SEDANG DIPUTAR
        # =================================================

        current = current_song.get(
            chat_id
        )

        if current:

            file_path = current.get(
                "file"
            )

            if (
                file_path
                and os.path.exists(file_path)
            ):

                try:
                    os.remove(
                        file_path
                    )
                except Exception:
                    pass

        # =================================================
        # HAPUS FILE ANTREAN
        # =================================================

        queue = music_queue.get(
            chat_id,
            []
        )

        for song in queue:

            file_path = song.get(
                "file"
            )

            if (
                file_path
                and os.path.exists(file_path)
            ):

                try:
                    os.remove(
                        file_path
                    )
                except Exception:
                    pass

        # =================================================
        # KOSONGKAN DATA
        # =================================================

        music_queue.pop(
            chat_id,
            None
        )

        current_song.pop(
            chat_id,
            None
        )

        # =================================================
        # KELUAR VOICE CHAT
        # =================================================

        try:

            await calls.leave_call(
                chat_id
            )

        except Exception:
            pass

        await message.reply_text(
            "⏹️ Musik dihentikan.\n"
            "🗑️ Antrean dikosongkan."
        )

    except Exception as e:

        await message.reply_text(
            "❌ Gagal menghentikan musik.\n\n"
            "Error:\n" + str(e)
        )

    finally:

        manual_change.discard(
            chat_id
        )


# =========================================================
# STREAM END
#
# Ketika lagu selesai, otomatis putar lagu berikutnya.
# =========================================================

async def stream_end_handler(
    _,
    update: StreamEnded
):

    chat_id = update.chat_id

    print("================================")
    print("STREAM SELESAI")
    print("Chat:", chat_id)
    print("================================")

    # Skip/stop manual ditangani oleh command masing-masing
    if chat_id in manual_change:

        print(
            "Stream end diabaikan "
            "karena perubahan manual."
        )

        return

    try:

        # Hapus file lagu sebelumnya
        old_song = current_song.get(
            chat_id
        )

        old_file = None

        if old_song:

            old_file = old_song.get(
                "file"
            )

        # =================================================
        # ADA ANTREAN?
        # =================================================

        queue = music_queue.get(
            chat_id,
            []
        )

        if queue:

            next_song = queue.pop(0)

            music_queue[chat_id] = queue

            print(
                "Otomatis lanjut:",
                next_song["title"]
            )

            await play_song(
                chat_id,
                next_song["title"],
                next_song["file"]
            )

            if (
                old_file
                and os.path.exists(old_file)
                and old_file != next_song["file"]
            ):

                try:
                    os.remove(
                        old_file
                    )

                except Exception as e:

                    print(
                        "Gagal hapus file lama:",
                        e
                    )

        else:

            # =================================================
            # ANTREAN HABIS
            # =================================================

            print(
                "Antrean habis:",
                chat_id
            )

            current_song.pop(
                chat_id,
                None
            )

            music_queue.pop(
                chat_id,
                None
            )

            if (
                old_file
                and os.path.exists(old_file)
            ):

                try:
                    os.remove(
                        old_file
                    )

                except Exception:
                    pass

            try:

                await bot.send_message(
                    chat_id,
                    "⏹️ Lagu selesai.\n"
                    "📋 Antrean sudah habis."
                )

            except Exception:
                pass

    except Exception as e:

        print("================================")
        print("ERROR STREAM END")
        print(type(e).__name__)
        print(str(e))
        print("================================")


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

        print(
            "Starting bot account..."
        )

        await bot.start()

        print(
            "BOT ACCOUNT AKTIF"
        )

        # =================================================
        # START USER
        # =================================================

        print(
            "Starting user account..."
        )

        await user.start()

        print(
            "USER ACCOUNT AKTIF"
        )

        # =================================================
        # START PYTGCALLS
        # =================================================

        print(
            "Starting PyTgCalls..."
        )

        calls = PyTgCalls(
            user
        )

        # =================================================
        # DAFTARKAN STREAM END
        # =================================================

        calls.on_update(
            fl.stream_end()
        )(
            stream_end_handler
        )

        await calls.start()

        print(
            "PYTGCALLS AKTIF"
        )

        # =================================================
        # SYSTEM CHECK
        # =================================================

        print("================================")
        print("SYSTEM CHECK")
        print(
            "ffmpeg  :",
            shutil.which("ffmpeg")
        )
        print(
            "ffprobe :",
            shutil.which("ffprobe")
        )
        print("================================")

        # =================================================
        # SIAP
        # =================================================

        print("================================")
        print("MUSIC BOT SIAP")
        print("QUEUE SYSTEM AKTIF")
        print("================================")

        await idle()

    except Exception as e:

        print("================================")
        print("MAIN ERROR")
        print(
            type(e).__name__
        )
        print(
            str(e)
        )
        print("================================")

    finally:

        print(
            "Stopping services..."
        )

        if calls is not None:

            try:
                await calls.stop()
            except Exception as e:
                print(
                    "CALLS STOP ERROR:",
                    e
                )

        try:

            await user.stop()

        except Exception as e:

            print(
                "USER STOP ERROR:",
                e
            )

        try:

            await bot.stop()

        except Exception as e:

            print(
                "BOT STOP ERROR:",
                e
            )

        print(
            "SERVICE BERHENTI"
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    asyncio.run(main())
