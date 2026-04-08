import logging
import subprocess
import os
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

def add_text_to_image(image_path, text="Nonton dari Link Bio ya"):
    """Menambahkan teks di tengah foto dengan background semi-transparan"""
    try:
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img, "RGBA")
        width, height = img.size
        # Font size adjustment
        font_size = int(width / 15)
        if font_size < 20: font_size = 20
        # Try multiple fonts for Windows/Linux support
        font_paths = ["arial.ttf", "DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "Ubuntu-R.ttf"]
        font = None
        for path in font_paths:
            try:
                font = ImageFont.truetype(path, font_size)
                break
            except:
                continue
        
        if not font:
            font = ImageFont.load_default()
        
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (width - text_width) / 2
        y = (height - text_height) / 2
        
        padding = 10
        draw.rectangle([x - padding, y - padding, x + text_width + padding, y + text_height + padding], fill=(0, 0, 0, 160))
        draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
        
        img.convert("RGB").save(image_path)
        return True
    except Exception as e:
        logger.error(f"Gagal mengedit foto: {str(e)}")
        return False

def convert_image_to_video(image_path, output_video_path, audio_path=None):
    """Mengonversi foto menjadi video MP4, bisa ditambahkan audio MP3"""
    try:
        if audio_path and os.path.exists(audio_path):
            # Jika ada audio: Gunakan audio tersebut (looping video atau cut audio)
            cmd = [
                'ffmpeg', '-y', '-loop', '1', '-i', image_path,
                '-i', audio_path,
                '-c:v', 'libx264', '-t', '15', '-pix_fmt', 'yuv420p',
                '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
                '-c:a', 'aac', '-shortest',
                output_video_path
            ]
            logging.info(f"Mengonversi foto ke video dengan audio: {audio_path}")
        else:
            # Jika tanpa audio: Video 5 detik tanpa suara
            cmd = [
                'ffmpeg', '-y', '-loop', '1', '-i', image_path,
                '-c:v', 'libx264', '-t', '5', '-pix_fmt', 'yuv420p',
                '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
                output_video_path
            ]
            logging.info("Mengonversi foto ke video tanpa audio kustom.")
            
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        logger.error(f"Gagal konversi video: {str(e)}")
        return False
