"""
AutoNews AI - Video Maker
Creates short-form videos (YouTube Shorts / Instagram Reels) using:
- Edge TTS (free, unlimited voice generation)
- FFmpeg (free video rendering)
- Pillow (free thumbnail/frame generation)
"""
import asyncio
import json
import logging
import subprocess
import textwrap
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import config

log = logging.getLogger(__name__)


# ── Text-to-Speech using Edge TTS (FREE, unlimited) ─────────
async def generate_voice(text: str, output_path: Path,
                         voice: str = "hi-IN-SwaraNeural") -> Path | None:
    """Generate voice audio from text using Microsoft Edge TTS (free)."""
    try:
        import edge_tts

        # Clean text — remove markers
        clean_text = text.replace("[PAUSE]", ",").replace("[pause]", ",")

        communicate = edge_tts.Communicate(clean_text, voice)
        await communicate.save(str(output_path))
        log.info(f"Voice generated: {output_path.name}")
        return output_path
    except ImportError:
        log.error("edge-tts not installed. Run: pip install edge-tts")
        return None
    except Exception as e:
        log.error(f"TTS error: {e}")
        return None


def generate_voice_sync(text: str, output_path: Path, voice: str = "hi-IN-SwaraNeural") -> Path | None:
    """Synchronous wrapper for voice generation."""
    return asyncio.run(generate_voice(text, output_path, voice))


# ── Create text frames using Pillow ──────────────────────────
def create_text_frame(text: str, output_path: Path,
                      width: int = 1080, height: int = 1920,
                      bg_color: str = "#0a0d0b",
                      text_color: str = "#e8ebe9",
                      accent_color: str = "#4ade80") -> Path:
    """Create a single video frame with text overlay."""
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Try to use a good font, fallback to default
    try:
        font_large = ImageFont.truetype("arial.ttf", 52)
        font_small = ImageFont.truetype("arial.ttf", 28)
        font_brand = ImageFont.truetype("arial.ttf", 32)
    except OSError:
        font_large = ImageFont.load_default()
        font_small = font_large
        font_brand = font_large

    # Draw gradient background overlay
    for y in range(height):
        alpha = int(255 * (y / height) * 0.3)
        draw.line([(0, y), (width, y)], fill=(10, 18, 12, alpha))

    # Draw accent bar at top
    draw.rectangle([(0, 0), (width, 6)], fill=accent_color)

    # Draw brand name
    draw.text((40, 60), config.CHANNEL_NAME, fill=accent_color, font=font_brand)

    # Draw main text (wrapped)
    wrapped = textwrap.fill(text, width=28)
    lines = wrapped.split("\n")
    y_pos = height // 2 - (len(lines) * 60) // 2
    for line in lines:
        draw.text((60, y_pos), line, fill=text_color, font=font_large)
        y_pos += 65

    # Draw CTA at bottom
    cta = f"Follow {config.CHANNEL_HANDLE}"
    draw.text((60, height - 120), cta, fill=accent_color, font=font_small)

    # Draw bottom bar
    draw.rectangle([(0, height - 6), (width, height)], fill=accent_color)

    img.save(str(output_path), quality=95)
    log.info(f"Frame created: {output_path.name}")
    return output_path


def create_video_frames(script_data: dict, output_dir: Path) -> list[Path]:
    """Create multiple frames from a script for the video."""
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    script_text = script_data.get("script", "")
    # Split by [PAUSE] markers
    segments = [s.strip() for s in script_text.split("[PAUSE]") if s.strip()]

    frame_paths = []
    for i, segment in enumerate(segments):
        frame_path = frames_dir / f"frame_{i:03d}.png"
        create_text_frame(segment, frame_path)
        frame_paths.append(frame_path)

    log.info(f"Created {len(frame_paths)} frames")
    return frame_paths


# ── Create thumbnail ─────────────────────────────────────────
def create_thumbnail(title: str, output_path: Path) -> Path:
    """Create a YouTube thumbnail."""
    width, height = 1280, 720
    img = Image.new("RGB", (width, height), "#0a0d0b")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 56)
        font_small = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
        font_small = font

    # Background gradient
    for y in range(height):
        r = int(10 + (y / height) * 20)
        g = int(13 + (y / height) * 30)
        b = int(11 + (y / height) * 15)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Accent border
    draw.rectangle([(0, 0), (width, 8)], fill="#4ade80")
    draw.rectangle([(0, height - 8), (width, height)], fill="#4ade80")

    # Title text
    wrapped = textwrap.fill(title, width=25)
    draw.text((60, height // 2 - 80), wrapped, fill="#ffffff", font=font)

    # Brand
    draw.text((60, height - 70), config.CHANNEL_NAME, fill="#4ade80", font=font_small)

    img.save(str(output_path), quality=95)
    log.info(f"Thumbnail created: {output_path.name}")
    return output_path


# ── Assemble video with FFmpeg ───────────────────────────────
def assemble_video(frames: list[Path], audio_path: Path | None,
                   output_path: Path, fps: int = 1) -> Path | None:
    """
    Assemble frames + audio into a video using FFmpeg.
    Each frame is shown for a few seconds based on audio length.
    """
    if not frames:
        log.error("No frames to assemble")
        return None

    # Check FFmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        log.error("FFmpeg not found! Install from https://ffmpeg.org/download.html")
        return None

    frames_dir = frames[0].parent

    # Create a concat file for FFmpeg
    concat_file = frames_dir / "concat.txt"
    duration_per_frame = 5  # default seconds per frame

    if audio_path and audio_path.exists():
        # Get audio duration
        probe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)
        ]
        try:
            result = subprocess.run(probe_cmd, capture_output=True, text=True)
            total_duration = float(result.stdout.strip())
            duration_per_frame = total_duration / max(len(frames), 1)
        except (ValueError, subprocess.CalledProcessError):
            duration_per_frame = 5

    with open(concat_file, "w") as f:
        for frame in frames:
            f.write(f"file '{frame.resolve()}'\n")
            f.write(f"duration {duration_per_frame:.2f}\n")
        # Repeat last frame (FFmpeg requirement)
        f.write(f"file '{frames[-1].resolve()}'\n")

    # Build FFmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
    ]

    if audio_path and audio_path.exists():
        cmd.extend(["-i", str(audio_path)])
        cmd.extend([
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-vf", f"scale={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT}",
            str(output_path),
        ])
    else:
        cmd.extend([
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-vf", f"scale={config.VIDEO_WIDTH}:{config.VIDEO_HEIGHT}",
            str(output_path),
        ])

    try:
        log.info(f"Assembling video: {output_path.name}")
        subprocess.run(cmd, capture_output=True, check=True, timeout=120)
        log.info(f"Video assembled: {output_path.name} ({output_path.stat().st_size / 1024:.0f} KB)")
        return output_path
    except subprocess.CalledProcessError as e:
        log.error(f"FFmpeg error: {e.stderr.decode()[:500]}")
        return None
    except subprocess.TimeoutExpired:
        log.error("FFmpeg timed out after 120s")
        return None


# ── Full video creation pipeline ─────────────────────────────
def create_video(script_data: dict) -> dict | None:
    """
    Full pipeline: script → voice → frames → video + thumbnail.
    Returns dict with paths to all outputs.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    title = script_data.get("source_title", "video")
    safe_title = "".join(c for c in title[:30] if c.isalnum() or c in " -_").strip().replace(" ", "_")
    video_id = f"{timestamp}_{safe_title}"

    # Create output directory for this video
    video_dir = config.VIDEOS_DIR / video_id
    video_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Generate voice
    audio_path = video_dir / "voice.mp3"
    script_text = script_data.get("script", "")
    voice_result = generate_voice_sync(script_text, audio_path)

    # Step 2: Create frames
    frames = create_video_frames(script_data, video_dir)

    # Step 3: Assemble video
    video_path = video_dir / f"{video_id}.mp4"
    video_result = assemble_video(frames, audio_path if voice_result else None, video_path)

    # Step 4: Create thumbnail
    thumb_path = config.THUMBNAILS_DIR / f"{video_id}_thumb.jpg"
    create_thumbnail(title, thumb_path)

    # Save metadata
    metadata = {
        "video_id": video_id,
        "title": title,
        "script": script_data,
        "audio_path": str(audio_path) if voice_result else None,
        "video_path": str(video_path) if video_result else None,
        "thumbnail_path": str(thumb_path),
        "frames_count": len(frames),
        "created_at": datetime.now().isoformat(),
        "status": "ready" if video_result else "failed",
    }
    meta_file = video_dir / "metadata.json"
    meta_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    log.info(f"Video creation {'completed' if video_result else 'failed'}: {video_id}")
    return metadata


if __name__ == "__main__":
    test_script = {
        "hook": "🔥 OpenAI ne GPT-5 ka date announce kar diya!",
        "script": "Breaking news! [PAUSE] OpenAI ne officially confirm kar diya hai ki GPT-5 Q3 2026 mein aayega. [PAUSE] Isme reasoning 10x better hogi aur hallucinations kam honge. [PAUSE] Follow @AutoNewsAI for daily tech updates!",
        "title_youtube": "🔥 GPT-5 Release Date CONFIRMED!",
        "source_title": "GPT-5 Release Date Confirmed by OpenAI",
    }
    result = create_video(test_script)
    if result:
        print(json.dumps(result, indent=2))
