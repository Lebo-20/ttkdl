import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import os
from config import TIKTOK_STATE_FILE

async def run():
    async with async_playwright() as p:
        # Launch browser with some extra arguments to avoid detection
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Apply stealth
        await Stealth().apply_stealth_async(page)
        
        print("Opening TikTok Login...")
        await page.goto("https://www.tiktok.com/login", wait_until="networkidle")
        
        print("\n" + "="*50)
        print("TIPS LOGIN:")
        print("1. Jika QR Code tidak muncul, refresh halaman (F5).")
        print("2. Jika masih gagal, coba login menggunakan Email/Phone.")
        print("3. Setelah masuk ke Home Page, kembali ke sini.")
        print("="*50 + "\n")
        
        input("Tekan ENTER di sini jika sudah berhasil login dan masuk ke Home TikTok...")
        
        # Save storage state
        await context.storage_state(path=TIKTOK_STATE_FILE)
        print(f"✅ Berhasil! Sesi login telah disimpan di {TIKTOK_STATE_FILE}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
