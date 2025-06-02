import os
import logging
import subprocess
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# Load .env
load_dotenv()

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ENV variables
API_ID = int(os.getenv("API_ID", "123456"))
API_HASH = os.getenv("API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")

# Flask setup
app = Flask(__name__)
@app.route('/')
def home():
    return '✅ Video Compressor Bot is Alive!'

def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

# Initialize bot
bot = Client("compressor_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ============ UTILITIES ============

def create_progress_bar(percentage):
    filled = int(percentage / 10)
    return "▰" * filled + "▱" * (10 - filled)

def human_readable(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

async def progress(current, total, message: Message):
    percent = current * 100 / total
    bar = create_progress_bar(percent)
    try:
        await message.edit_text(
            f"🔄 Progress: {bar} `{percent:.1f}%`\n"
            f"📦 {human_readable(current)} of {human_readable(total)}"
        )
    except:
        pass

def compress_video(input_file: str, output_file: str) -> bool:
    try:
        command = [
            "ffmpeg", "-i", input_file,
            "-vcodec", "libx264", "-crf", "28", "-preset", "slow",
            "-acodec", "aac", "-b:a", "128k",
            "-vf", "scale=-2:720",
            "-movflags", "+faststart",
            output_file
        ]
        subprocess.run(command, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        return True
    except Exception as e:
        logger.error(f"Compression Error: {e}")
        return False

# ============ COMMANDS ============

@bot.on_message(filters.command("start"))
async def start(client, message):
    buttons = [
        [InlineKeyboardButton("📢 Channel", url="https://t.me/RM_Movie_Flix")],
        [InlineKeyboardButton("💬 Support", url="t.me/RM_Supports")],
        [InlineKeyboardButton("👤 Developer", url="https://t.me/RahatMx")]
    ]
    await message.reply_text(
        "**🎥 Video Compressor Bot**\n\n"
        "🌀 Just send a video and I'll compress it for you.\n"
        "📦 Max Size: 2GB\n"
        "💡 Super Fast Speed`\n\n"
        "**Send a video now!**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ============ VIDEO HANDLER ============

@bot.on_message(filters.video | filters.document)
async def handle_video(client, message: Message):
    try:
        file = message.video or message.document
        if not file.mime_type.startswith("video/"):
            return

        if file.file_size > 2 * 1024 * 1024 * 1024:
            return await message.reply_text("❌ File too large. Limit is 2GB.")

        msg = await message.reply_text("📥 Downloading your video...")

        input_path = f"downloads/input_{file.file_unique_id}.mp4"
        orig_name = os.path.splitext(file.file_name or "video")[0]
        final_name = f"{orig_name}_Vid_fast_compress_bot.mp4"
        output_path = f"downloads/{final_name}"

        os.makedirs("downloads", exist_ok=True)

        await file.download(input_path, progress=progress, progress_args=(msg, file.file_size))

        await msg.edit_text("⚙️ Compressing the video... Please wait.")
        success = compress_video(input_path, output_path)

        if not success:
            return await msg.edit_text("❌ Compression failed.")

        await msg.edit_text("📤 Uploading compressed video...")

        await message.reply_video(
            video=output_path,
            caption="✅ Here's your compressed video!\n\n🤖 by @Vid_fast_compress_bot",
            file_name=final_name,
            supports_streaming=True,
            progress=progress,
            progress_args=(msg, os.path.getsize(output_path))
        )
        await msg.delete()

    except Exception as e:
        logger.error(f"Error: {e}")
        await message.reply_text("❌ Something went wrong!")
    finally:
        for path in [input_path, output_path]:
            if os.path.exists(path):
                os.remove(path)

# ============ RUN ============

if __name__ == '__main__':
    Thread(target=run_flask).start()
    logger.info("🚀 Bot is running...")
    bot.run()
