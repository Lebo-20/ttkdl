import os
import uuid
import logging
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler, Application
from config import TELEGRAM_TOKEN, DOWNLOAD_DIR, ADMIN_IDS, POST_INTERVAL_HOURS, ALLOWED_CHANNELS

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

upload_queue = None
CUSTOM_AUDIO_PATH = os.path.join(DOWNLOAD_DIR, "active_bgm.mp3")

def is_admin(user_id):
    return not ADMIN_IDS or user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.channel_post
    await msg.reply_text(
        "🎧 **Manajemen Musik Bot**\n\n"
        "1. Kirim MP3 dangan `/setmusic` (balas file) untuk lagu latar.\n"
        "2. `/unmusic` untuk hapus lagu latar.\n"
        "3. `/cd` untuk cek sisa cooldown.\n"
        "4. `/resetcd` untuk paksa reset cooldown.\n"
        "5. `/update` untuk tarik update dari GitHub.\n"
        "6. `/id` untuk cek ID chat/channel ini.\n"
        "7. `/list` untuk cek daftar channel diizinkan.\n"
        "8. Kirim foto/video untuk posting ke TikTok.",
        parse_mode="Markdown"
    )

async def set_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengatur musik latar dengan perintah /setmusic"""
    msg = update.message or update.channel_post
    if not msg: return
    if msg.chat.type == "private" and not is_admin(update.effective_user.id): return

    # Cek apakah ini diletakkan sebagai caption atau balasan (reply)
    target_msg = msg.reply_to_message if msg.reply_to_message else msg
    audio = target_msg.audio or target_msg.voice

    if not audio:
        await msg.reply_text("❌ Silakan balas (reply) file MP3 dengan perintah `/setmusic`.")
        return

    status_msg = await msg.reply_text("🎵 Sedang mendownload musik pilihan Anda...")
    try:
        new_file = await context.bot.get_file(audio.file_id)
        await new_file.download_to_drive(CUSTOM_AUDIO_PATH)
        await status_msg.edit_text("✅ **Musik Berhasil Diset!** Semua postingan foto berikutnya akan menggunakan lagu ini.", parse_mode="Markdown")
    except Exception as e:
        await status_msg.edit_text(f"❌ Gagal menyimpan musik: {e}")

async def unmusic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menghapus musik latar aktif dengan /unmusic"""
    msg = update.message or update.channel_post
    if os.path.exists(CUSTOM_AUDIO_PATH):
        try:
            os.remove(CUSTOM_AUDIO_PATH)
            await msg.reply_text("🗑 **Musik latar berhasil dihapus.** Bot kembali ke mode tanpa musik kustom.")
        except Exception as e:
            await msg.reply_text(f"❌ Gagal menghapus file: {e}")
    else:
        await msg.reply_text("ℹ️ Tidak ada musik kustom yang aktif saat ini.")

async def reset_cd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset cooldown posting dengan /resetcd"""
    msg = update.message or update.channel_post
    if not msg: return
    if msg.chat.type == "private" and not is_admin(update.effective_user.id): return
    
    upload_queue.reset_cooldown()
    await msg.reply_text("✅ **Cooldown berhasil di-reset!** Bot akan segera memproses antrean (jika ada).", parse_mode="Markdown")

async def git_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update bot dari github dengan /update"""
    msg = update.message or update.channel_post
    if not msg: return
    if msg.chat.type == "private" and not is_admin(update.effective_user.id): return
    
    status_msg = await msg.reply_text("🔄 Sedang mengambil update dari GitHub...")
    try:
        # Menjalankan git pull
        result = subprocess.run(["git", "pull"], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            output = result.stdout if result.stdout.strip() else "Sudah versi terbaru."
            await status_msg.edit_text(f"✅ **Update Berhasil!**\n\n```\n{output}\n```\nBot perlu direstart untuk menerapkan kode baru.", parse_mode="Markdown")
        else:
            await status_msg.edit_text(f"❌ **Gagal Update!**\n\n```\n{result.stderr}\n```", parse_mode="Markdown")
    except Exception as e:
        await status_msg.edit_text(f"❌ Terjadi kesalahan: {e}")

async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan daftar channel yang diizinkan"""
    msg = update.message or update.channel_post
    if not msg: return
    if msg.chat.type == "private" and not is_admin(update.effective_user.id): return

    text = "📋 **Daftar Channel Diizinkan:**\n\n"
    if not ALLOWED_CHANNELS:
        text += "_Tidak ada channel yang terdaftar._"
    else:
        for cid in ALLOWED_CHANNELS:
            text += f"• `{cid}`\n"
    
    await msg.reply_text(text, parse_mode="Markdown")

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.channel_post
    if not msg: return
    
    chat_id = msg.chat_id
    # Jika bukan admin di private chat DAN bukan dari channel yang diizinkan, abaikan
    is_allowed = chat_id in ALLOWED_CHANNELS
    is_admin_user = msg.chat.type == "private" and is_admin(update.effective_user.id if update.effective_user else 0)
    
    if not is_allowed and not is_admin_user:
        return

    # Skip if it's a command like /setmusic
    if msg.text and msg.text.startswith('/'): return
    if msg.chat.type == "private" and not is_admin(update.effective_user.id): return

    video = msg.video
    photo = msg.photo[-1] if msg.photo else None
    if not video and not photo: return
    if video and video.file_size > 100 * 1024 * 1024: return

    chat_id = msg.chat_id
    message_id = msg.message_id
    user_caption = msg.caption or ""
    file_id = video.file_id if video else photo.file_id
    temp_path = os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}{'.mp4' if video else '.jpg'}")

    status_msg = await msg.reply_text("📥 Menyiapkan bahan...")
    try:
        from bot_logic import add_text_to_image, convert_image_to_video
        new_file = await context.bot.get_file(file_id)
        await new_file.download_to_drive(temp_path)
        
        final_video_path = os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}.mp4")
        if photo:
            await status_msg.edit_text("🎨 Mengolah Foto + Teks + Musik...")
            add_text_to_image(temp_path)
            # Hanya gunakan musik jika file-nya ada (setelah /setmusic)
            audio_for_video = CUSTOM_AUDIO_PATH if os.path.exists(CUSTOM_AUDIO_PATH) else None
            
            if not convert_image_to_video(temp_path, final_video_path, audio_for_video):
                raise Exception("Proses konversi gagal.")
            
            if os.path.exists(temp_path): os.remove(temp_path)
        else:
            os.rename(temp_path, final_video_path)
        
        queue_pos = await upload_queue.add_job(final_video_path, chat_id, message_id, user_caption)
        await status_msg.edit_text(f"📝 Antrean diperbarui! (Posisi: {queue_pos}). Jeda: {POST_INTERVAL_HOURS} jam.")

    except Exception as e:
        if "File is too big" not in str(e):
            await status_msg.edit_text(f"❌ Error: {e}")

async def auto_status_update(context: ContextTypes.DEFAULT_TYPE):
    if not upload_queue: return
    title, count = upload_queue.get_next_job_info()
    cd_text = upload_queue.get_cooldown_text()
    music_status = "🎵 Musik Kustom Aktif" if os.path.exists(CUSTOM_AUDIO_PATH) else "🔈 Musik Kustom: OFF"
    
    if count > 0:
        text = f"📊 **[STATUS UPDATE]**\n\n📌 **Selanjutnya:** `{title}`\n📦 **Antrean:** {count} file\n{music_status}\n{cd_text}"
    else:
        text = f"📊 **[STATUS UPDATE]**\n\nAntrean kosong.\n{music_status}\n{cd_text}"
    
    for chat_id in ALLOWED_CHANNELS:
        try: await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        except: pass

async def post_init(application: Application):
    global upload_queue
    from queue_manager import UploadQueue
    upload_queue = UploadQueue(application.bot)
    upload_queue.start()
    if application.job_queue:
        application.job_queue.run_repeating(auto_status_update, interval=1800, first=10)
    else:
        print("⚠️ Warning: JobQueue is not available. Auto status updates disabled.")

def main():
    from config import TELEGRAM_TOKEN
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", lambda u, c: u.effective_message.reply_text(f"📍 **Chat ID:** `{u.effective_chat.id}`\n**Type:** {u.effective_chat.type}", parse_mode="Markdown")))
    application.add_handler(CommandHandler("cd", lambda u, c: u.effective_message.reply_text(upload_queue.get_cooldown_text(), parse_mode="Markdown")))
    application.add_handler(CommandHandler("list", list_channels))
    application.add_handler(CommandHandler("setmusic", set_music))
    application.add_handler(CommandHandler("unmusic", unmusic))
    application.add_handler(CommandHandler("resetcd", reset_cd))
    application.add_handler(CommandHandler("update", git_update))
    
    media_filter = (filters.VIDEO | filters.PHOTO) & ~filters.COMMAND
    application.add_handler(MessageHandler(media_filter, handle_media))
    application.add_handler(MessageHandler(filters.ChatType.CHANNEL & media_filter, handle_media))

    print("Bot Aktif (V4.0: Audio Management Ready)")
    application.run_polling()

if __name__ == "__main__":
    main()
