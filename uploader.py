import asyncio
import random
import logging
import os
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from config import TIKTOK_STATE_FILE, HEADLESS, CAPTIONS, HASHTAGS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def dismiss_modals(page):
    try:
        await page.mouse.click(10, 10)
        dismiss_buttons = [
            'button:has-text("Got it")',
            'button:has-text("OK")',
            'button:has-text("Not now")',
            'button:has-text("Dismiss")',
            'i[class*="close"]',
            '[aria-label*="Close"]',
            'svg[class*="close"]',
            'div[class*="close"]'
        ]
        for selector in dismiss_buttons:
            btn = page.locator(selector).first
            if await btn.count() > 0 and await btn.is_visible():
                await btn.click()
                logging.info(f"Pop-up ditutup: {selector}")
                await page.wait_for_timeout(1000)
    except:
        pass

async def upload_video(video_path, caption=None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        
        context = await browser.new_context(
            storage_state=TIKTOK_STATE_FILE,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        try:
            logging.info("Membuka TikTok Studio...")
            await page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded", timeout=90000)
            await page.wait_for_timeout(5000)
            await dismiss_modals(page)

            # Pilih file via physical click
            logging.info("Mengeklik tombol Select Video...")
            try:
                await page.wait_for_selector('button:has-text("Select video"), button:has-text("Select file")', timeout=30000)
                async with page.expect_file_chooser() as fc_info:
                    await page.click('button:has-text("Select video"), button:has-text("Select file")', force=True)
                file_chooser = await fc_info.value
                await file_chooser.set_files(video_path)
            except:
                file_input = page.locator('input[type="file"]').first
                await file_input.set_input_files(video_path)

            logging.info("Tunggu TikTok merespons file (max 3 menit)...")
            await page.wait_for_selector('div[contenteditable="true"]', timeout=180000)
            await dismiss_modals(page)

            # --- CAPTION ---
            if caption and len(caption.strip()) > 0:
                full_caption = f"{caption}\n\n{HASHTAGS}"
            else:
                full_caption = f"{random.choice(CAPTIONS)}\n\n{HASHTAGS}"
            
            caption_box = page.locator('div[contenteditable="true"]')
            await caption_box.click()
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await caption_box.fill(full_caption)
            
            # --- MUSIC ---
            try:
                music_btn = page.locator('div:has-text("Sounds"), button:has-text("music")').first
                if await music_btn.is_visible():
                    await music_btn.click()
                    await page.wait_for_timeout(3000)
                    song = page.locator('div[class*="SongItem"], [data-e2e="music-item"]').first
                    if await song.is_visible():
                        await song.click()
                        logging.info("Musik populer ditambahkan.")
            except: pass

            # --- UNCHECK CONTENT CHECK LITE ---
            try:
                switch = page.locator('div:has-text("Content check lite") >> [role="switch"]').first
                if await switch.is_visible() and (await switch.get_attribute("aria-checked")) == "true":
                    await switch.click()
                    logging.info("Content check lite dimatikan.")
            except: pass

            await page.wait_for_timeout(5000)
            await dismiss_modals(page)

            # --- POST ---
            logging.info("Mencoba scroll ke bawah untuk menemukan tombol Post...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)
            
            post_btn = page.locator('[data-e2e="post-button"], button:has-text("Post")').last # Ambil yang paling bawah
            
            logging.info("Menunggu tombol Post aktif...")
            for _ in range(40): # Tunggu hingga 80 detik untuk tombol aktif
                if await post_btn.is_enabled() and await post_btn.is_visible(): break
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)") # Pastikan tetap di bawah
                await page.wait_for_timeout(2000)
                await dismiss_modals(page)
            
            logging.info("Tombol Post aktif. Mengeksekusi pengeklikan...")
            await page.evaluate('(btn) => { btn.scrollIntoView(); btn.click(); }', await post_btn.element_handle())
            
            # Cari konfirmasi (Bisa muncul berkali-kali)
            for _ in range(3):
                await page.wait_for_timeout(3000)
                confirm_selectors = ['button:has-text("Post now")', 'button:has-text("Post anyway")', 'div[role="dialog"] button:has-text("Post")']
                clicked_modal = False
                for sel in confirm_selectors:
                    btn = page.locator(sel).last
                    if await btn.count() > 0 and await btn.is_visible():
                        logging.info(f"Klik konfirmasi tambahan: {sel}")
                        await page.evaluate('(b) => b.click()', await btn.element_handle())
                        clicked_modal = True
                        break
                if not clicked_modal: break # Jika tidak ada modal lagi, stop loop konfirmasi

            # --- VERIFIKASI SUKSES ---
            logging.info("Memverifikasi apakah postingan benar-benar terkirim...")
            success = False
            for i in range(25): # Tunggu hingga ~1 menit
                if "/manage-posts" in page.url or "/content" in page.url:
                    success = True
                    break
                
                # Indikator teks di dashboard sukses
                indicators = ['text="Manage your posts"', 'text="Content under review"', 'text="Posts (Created on)"', 'text="Video is being processed"']
                for ind in indicators:
                    if await page.locator(ind).count() > 0:
                        success = True
                        break
                if success: break

                # Retry konfirmasi jika masih macet di halaman upload
                confirm_selectors = ['button:has-text("Post anyway")', 'button:has-text("Post now")', 'div[role="dialog"] button:has-text("Post")']
                for sel in confirm_selectors:
                    btn = page.locator(sel).last
                    if await btn.count() > 0 and await btn.is_visible():
                        logging.info(f"Retrying konfirmasi akhir...")
                        await page.evaluate('(b) => b.click()', await btn.element_handle())
                
                await page.wait_for_timeout(3000)

            await page.screenshot(path="last_upload_result.png")
            if success:
                logging.info("✅ Postingan terverifikasi sukses muncul di sistem TikTok!")
                return True, "Berhasil! Video sudah terverifikasi muncul di dashboard TikTok."
            else:
                logging.error("❌ Gagal verifikasi: Halaman tidak berpindah ke dashboard sukses.")
                return False, "Eror: Tombol diklik tapi video sepertinya tertahan/ditolak TikTok. Cek last_upload_result.png"

        except Exception as e:
            logging.error(f"Error: {e}")
            await page.screenshot(path="error_final.png")
            return False, str(e)
        finally:
            await browser.close()
