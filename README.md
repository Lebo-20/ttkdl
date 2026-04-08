# Telegram to TikTok Uploader Bot

Sistem otomatisasi untuk mengambil video dari Telegram dan mengunggahnya ke TikTok menggunakan Python, Playwright, dan python-telegram-bot.

## 🚀 Fitur

- **Telegram Bot**: Menerima video dan memberikan status progres.
- **Queue System**: Antrean upload otomatis dengan delay anti-spam (30-60 detik).
- **Auto Login**: Menggunakan `storage_state` Playwright untuk menyimpan sesi login.
- **Auto Caption**: Generate caption acak dan hashtag otomatis.
- **Error Handling**: Menangani gagal download, session expired, dan gagal upload.

## 🛠️ Persiapan

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Konfigurasi**:
   - Buka file `.env` dan isi `TELEGRAM_TOKEN` dengan token bot Anda dari @BotFather.
   - Edit `config.py` jika ingin mengubah list caption atau hashtag.

3. **Login TikTok**:
   Anda harus melakukan login manual sekali untuk menyimpan cookie/sesi.
   ```bash
   python login.py
   ```
   - Jendela browser akan terbuka.
   - Login ke akun TikTok Anda.
   - Setelah masuk ke halaman utama, kembali ke terminal dan tekan **Enter**.
   - File `tiktok_state.json` akan terbuat.

## 🤖 Cara Menjalankan

Setelah setup selesai, jalankan bot utama:
```bash
python bot.py
```

## 📂 Struktur Folder

- `bot.py`: Handler utama untuk Telegram.
- `uploader.py`: Logika upload TikTok menggunakan Playwright.
- `queue_manager.py`: Mengatur antrean dan worker background.
- `login.py`: Script untuk capture sesi login.
- `config.py`: Pengaturan global.
- `downloads/`: Folder sementara untuk video yang diunduh.

## ⚠️ Catatan Penting
- Gunakan `HEADLESS=False` di `.env` jika ingin melihat proses upload di browser secara visual.
- Pastikan akun TikTok Anda tidak terkena limit shadowban jika mengunggah terlalu banyak video dalam waktu singkat.
