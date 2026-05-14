"""
AutoNews AI - Video Maker v3.1 (Ultra Reliable)
Real video generation with strong error recovery and chunked processing.
"""

import asyncio
import json
import logging
import subprocess
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from PIL import Image, ImageDraw, ImageFont

import config

log = logging.getLogger(__name__)

# ========================== CONFIG ==========================
VIDEO_WIDTH = getattr(config, "VIDEO_WIDTH", 1080)
VIDEO_HEIGHT = getattr(config, "VIDEO_HEIGHT", 1920)
FPS = 30
DEFAULT_FRAME_DURATION = 4.5

TTS_VOICE = getattr(config, "TTS_VOICE", "hi-IN-SwaraNeural")
TTS_FALLBACK = "en-US-JennyNeural"

# ========================== DEPENDENCY CHECK ==========================
def check_dependencies() -> bool:
    """Check required tools."""
    try:
        if not subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5).returncode == 0:
            log.error("❌ FFmpeg not found. Video creation will fail.")
            return False
    except FileNotFoundError:
        log.error("❌ FFmpeg not found in PATH. Video creation will fail.")
        return False
        
    try:
        import edge_tts
    except ImportError:
        log.warning("edge-tts not installed → videos will be silent")
    return True


# ========================== TTS ==========================
async def generate_voice_async(text: str, output_path: Path) -> Optional[Path]:
    try:
        import edge_tts
        clean_text = text.replace("[PAUSE]", ", ").replace("[pause]", ", ")
        clean_text = " ".join(clean_text.split())

        communicate = edge_tts.Communicate(clean_text, voice=TTS_VOICE)
        await communicate.save(str(output_path))

        if output_path.stat().st_size > 2048:
            log.info(f"🎤 Voice generated ({output_path.stat().st_size/1024:.1f} KB)")
            return output_path
    except Exception as e:
        log.warning(f"Primary voice failed: {e}")
        # Try fallback voice
        try:
            communicate = edge_tts.Communicate(clean_text, voice=TTS_FALLBACK)
            await communicate.save(str(output_path))
            return output_path
        except Exception as e2:
            log.error(f"All TTS attempts failed: {e2}")
    return None


# ========================== FRAME GENERATION ==========================
def get_font(size: int):
    """Robust font loading across platforms."""
    font_paths = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "arialbd.ttf", "Arial-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def create_text_frame(text: str, output_path: Path) -> Path:
    """Create visually rich frame."""
    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), "#0a0a0a")
    draw = ImageDraw.Draw(img)

    font_large = get_font(58)
    font_med = get_font(34)
    font_small = get_font(28)

    # Subtle gradient
    for y in range(VIDEO_HEIGHT):
        shade = int(15 + (y / VIDEO_HEIGHT) * 25)
        draw.line([(0, y), (VIDEO_WIDTH, y)], fill=(shade, shade, shade))

    draw.rectangle([(0, 0), (VIDEO_WIDTH, 10)], fill="#22c55e")

    # Brand
    draw.text((50, 45), getattr(config, "CHANNEL_NAME", "AutoNews AI").upper(),
              fill="#22c55e", font=font_small)

    # Main content
    wrapped = textwrap.fill(text, width=32)
    lines = wrapped.split("\n")
    y = (VIDEO_HEIGHT // 2) - (len(lines) * 75) // 2

    for line in lines:
        draw.text((70, y), line, fill="#f8fafc", font=font_large, stroke_width=2, stroke_fill="#0a0a0a")
        y += 82

    # CTA
    cta = f"Follow {getattr(config, 'CHANNEL_HANDLE', '@AutoNewsAI')} 🔥"
    draw.text((70, VIDEO_HEIGHT - 130), cta, fill="#bef575", font=font_med)

    draw.rectangle([(0, VIDEO_HEIGHT - 10), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill="#22c55e")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95)
    return output_path


def create_video_frames(script_data: Dict, output_dir: Path) -> List[Path]:
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    script = script_data.get("script", "") or script_data.get("hook", "")
    segments = [s.strip() for s in script.split("[PAUSE]") if s.strip()]

    if not segments:
        segments = [script[:280]]

    frame_paths = []
    for i, segment in enumerate(segments):
        frame_path = frames_dir / f"frame_{i:03d}.png"
        create_text_frame(segment, frame_path)
        frame_paths.append(frame_path)

    log.info(f"🖼️ Created {len(frame_paths)} frames")
    return frame_paths


# ========================== THUMBNAIL ==========================
def create_thumbnail(title: str, output_path: Path) -> Optional[Path]:
    try:
        img = Image.new("RGB", (1280, 720), "#0f172a")
        draw = ImageDraw.Draw(img)
        font_big = get_font(68)
        font_small = get_font(32)

        draw.rectangle([(0, 0), (1280, 12)], fill="#22c55e")
        wrapped = textwrap.fill(title, width=24)
        draw.text((80, 180), wrapped, fill="#f1f5f9", font=font_big, stroke_width=3, stroke_fill="#000")

        draw.text((80, 560), getattr(config, "CHANNEL_NAME", "AutoNews AI"), fill="#67e8f9", font=font_small)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, quality=98)
        return output_path
    except Exception as e:
        log.error(f"Thumbnail failed: {e}")
        return None


# ========================== VIDEO ASSEMBLY ==========================
def assemble_video(frames: List[Path], audio_path: Optional[Path], output_path: Path) -> Optional[Path]:
    if not frames:
        return None

    temp_dir = output_path.parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    concat_file = temp_dir / "concat.txt"

    audio_duration = None
    if audio_path and audio_path.exists():
        try:
            result = subprocess.run([
                "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                "-of", "csv=p=0", str(audio_path)
            ], capture_output=True, text=True, timeout=8)
            audio_duration = float(result.stdout.strip())
        except Exception:
            pass

    frame_duration = (audio_duration / len(frames)) if audio_duration else DEFAULT_FRAME_DURATION

    # Write concat list
    with open(concat_file, "w", encoding="utf-8") as f:
        for frame in frames:
            f.write(f"file '{frame.resolve()}'\n")
            f.write(f"duration {frame_duration:.3f}\n")
        f.write(f"file '{frames[-1].resolve()}'\n")  # Repeat last frame

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
        "-r", str(FPS)
    ]

    if audio_path and audio_path.exists():
        cmd.extend(["-i", str(audio_path), "-c:a", "aac", "-b:a", "192k", "-shortest"])

    cmd.append(str(output_path))

    try:
        log.info("🎬 Rendering final video...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=200)

        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 300_000:
            log.info(f"✅ Video successfully created ({output_path.stat().st_size / (1024*1024):.2f} MB)")
            return output_path
        else:
            log.error(f"FFmpeg failed: {result.stderr[-400:]}")
            return None
    except Exception as e:
        log.exception(f"Video assembly failed: {e}")
        return None


# ========================== MAIN FUNCTION ==========================
def create_video(script_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Main pipeline with strong error recovery."""
    if not check_dependencies():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    title = script_data.get("source_title") or script_data.get("title_youtube", "News Update")
    safe_title = "".join(c for c in title[:35] if c.isalnum() or c in " -_").strip().replace(" ", "_")

    video_id = f"{timestamp}_{safe_title}"
    video_dir = Path(config.VIDEOS_DIR) / video_id
    video_dir.mkdir(parents=True, exist_ok=True)

    log.info(f"🚀 Starting video creation: {title[:70]}...")

    # 1. Voice
    audio_path = video_dir / "voice.mp3"
    voice_result = asyncio.run(generate_voice_async(script_data.get("script", ""), audio_path))

    # 2. Frames
    frames = create_video_frames(script_data, video_dir)
    if not frames:
        log.error("Frame generation failed")
        return None

    # 3. Final Video
    final_video = video_dir / f"{video_id}.mp4"
    video_result = assemble_video(frames, voice_result, final_video)

    # 4. Thumbnail
    thumb_path = Path(config.THUMBNAILS_DIR) / f"{video_id}_thumb.jpg"
    create_thumbnail(title, thumb_path)

    metadata = {
        "video_id": video_id,
        "title": title,
        "status": "ready" if video_result else "partial",
        "video_path": str(video_result) if video_result else None,
        "audio_path": str(voice_result) if voice_result else None,
        "thumbnail_path": str(thumb_path),
        "frames_count": len(frames),
        "created_at": datetime.now().isoformat(),
    }

    (video_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    if video_result:
        log.info(f"🎉 FULL SUCCESS: {final_video.name}")
    else:
        log.warning("⚠️ Video created partially (check logs)")

    return metadata


if __name__ == "__main__":
    test_script = {
        "script": "Breaking news! [PAUSE] OpenAI ne GPT-5 ke release date ki confirmation kar di hai Q3 2026 mein. [PAUSE] Bahut badi update aane wali hai.",
        "source_title": "GPT-5 Release Date Confirmed",
        "title_youtube": "GPT-5 Release Date CONFIRMED! 🔥"
    }

    result = create_video(test_script)
    if result and result.get("video_path"):
        print(f"\n✅ Video ready: {result['video_path']}")
    else:
        print("\n❌ Failed to create video.")