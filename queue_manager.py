import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from config import POST_INTERVAL_HOURS

class UploadQueue:
    def __init__(self, bot):
        self.bot = bot
        self.queue = asyncio.Queue()
        self.worker_task = None
        self.next_post_at = None

    async def add_job(self, video_path, chat_id, message_id, caption):
        job = {
            "video_path": video_path,
            "chat_id": chat_id,
            "message_id": message_id,
            "caption": caption
        }
        await self.queue.put(job)
        return self.queue.qsize()

    def get_next_job_info(self):
        count = self.queue.qsize()
        if count == 0: return None, 0
        try:
            next_job = self.queue._queue[0]
            title = next_job.get("caption", "Tanpa Judul")
            if not title.strip(): title = "Media"
            title = title.split("\n")[0][:40]
            return title, count
        except: return "Pending...", count

    def get_cooldown_text(self):
        if not self.next_post_at or datetime.now() >= self.next_post_at:
            return "Bot siap memproses antrean berikutnya!"
        remaining = self.next_post_at - datetime.now()
        mm, ss = divmod(remaining.seconds, 60)
        hh, mm = divmod(mm, 60)
        return f"⏳ Cooldown: **{hh}j {mm}m {ss}s**."

    async def worker(self):
        logging.info("Worker started.")
        while True:
            job = await self.queue.get()
            video_path = job["video_path"]
            chat_id = job["chat_id"]
            message_id = job["message_id"]
            caption = job["caption"]

            success = False
            try:
                # Cooldown check
                if self.next_post_at and datetime.now() < self.next_post_at:
                    wait_sec = (self.next_post_at - datetime.now()).total_seconds()
                    await asyncio.sleep(wait_sec)

                logging.info(f"Processing: {video_path}")
                await self.bot.send_message(chat_id=chat_id, text="🚀 Memulai proses upload...", reply_to_message_id=message_id)
                
                from uploader import upload_video
                success, message = await upload_video(video_path, caption)
                
                status_text = f"✅ [Laporan]\n{message}" if success else f"❌ [Gagal]\n{message}"
                try:
                    await self.bot.send_message(chat_id=chat_id, text=status_text, reply_to_message_id=message_id)
                except: pass

                if success and os.path.exists(video_path):
                    os.remove(video_path)

            except Exception as e:
                logging.error(f"Worker Exception: {str(e)}")
            
            finally:
                # Jeda posting berikutnya
                if success:
                    wait_sec = POST_INTERVAL_HOURS * 3600
                else:
                    wait_sec = 60 # Skip cepat jika gagal
                
                self.next_post_at = datetime.now() + timedelta(seconds=wait_sec)
                self.queue.task_done()
                if not success:
                    logging.info("Gagal. Skipping ke selanjutnya dalam 1 menit...")
                    await asyncio.sleep(60)

    def reset_cooldown(self):
        self.next_post_at = datetime.now()

    def start(self):
        if self.worker_task is None:
            self.worker_task = asyncio.create_task(self.worker())
