from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path

from openai import OpenAI

from .models import GrabResult

FRAME_INTERVAL_SEC = int(os.getenv("FRAME_INTERVAL_SEC", os.getenv("LINK_GRABBER_FRAME_INTERVAL_SEC", "4")))
FRAME_MAX = int(os.getenv("FRAME_MAX", os.getenv("LINK_GRABBER_FRAME_MAX", "40")))


async def _run(cmd: list[str]) -> None:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(stderr.decode("utf-8", errors="replace")[-2000:])


async def extract_frames(video: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = out_dir / "frame_%04d.jpg"
    vf = f"fps=1/{FRAME_INTERVAL_SEC}"
    await _run(["ffmpeg", "-y", "-i", str(video), "-vf", vf, "-frames:v", str(FRAME_MAX), str(pattern)])
    return sorted(out_dir.glob("frame_*.jpg"))


async def extract_audio(video: Path, audio_path: Path) -> Path:
    await _run(["ffmpeg", "-y", "-i", str(video), "-vn", "-acodec", "libmp3lame", str(audio_path)])
    return audio_path


async def transcribe(video: Path, transcript_path: Path) -> Path:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for transcription. Use --no-transcript to skip.")
    audio = transcript_path.with_suffix(".mp3")
    await extract_audio(video, audio)

    def _call() -> str:
        client = OpenAI()
        with audio.open("rb") as fh:
            result = client.audio.transcriptions.create(
                model=os.getenv("WHISPER_MODEL", "whisper-1"),
                file=fh,
            )
        return result.text or ""

    text = await asyncio.to_thread(_call)
    transcript_path.write_text(text.strip() + "\n", encoding="utf-8")
    return transcript_path


async def comprehend_video(result: GrabResult, no_transcript: bool, no_frames: bool) -> None:
    if not result.video or not result.root:
        return
    if not shutil_available("ffmpeg"):
        raise RuntimeError("ffmpeg is required for video comprehension")
    if not no_frames:
        result.frames = await extract_frames(result.video, result.root / "frames")
    if not no_transcript:
        result.transcript = await transcribe(result.video, result.root / "transcript.txt")


def shutil_available(command: str) -> bool:
    try:
        subprocess.run([command, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except OSError:
        return False
    return True
