import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Settings
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_BOT_TOKEN_HERE")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
ADMIN_IDS = [int(i.strip()) for i in os.getenv("ADMIN_IDS", "").split(",") if i.strip()]

# TikTok Settings
TIKTOK_STATE_FILE = "tiktok_state.json"
HEADLESS = os.getenv("HEADLESS", "False").lower() == "true"
UPLOAD_DELAY_MIN = 30  # seconds
UPLOAD_DELAY_MAX = 60  # seconds

# Pengaturan Penjadwalan (Jam)
POST_INTERVAL_HOURS = 0.5  # Posting setiap 30 menit sekali
ALLOWED_CHANNELS = [-1001234567890] # Masukkan ID Channel yang diizinkan di sini

# Captions and Hashtags
CAPTIONS = [
    "Check out this amazing video!",
    "Bikin baper sih ini..",
    "POV: Ketika drama favoritmu tayang.",
    "Jangan lupa klik like dan follow ya!",
    "Rekomendasi hari ini.",
]

HASHTAGS = "#fyp #viral #tiktokindonesia #drama"

# Paths
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
