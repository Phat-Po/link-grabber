from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from .archive import save_obsidian
from .comprehend import comprehend_video
from .detect import detect_platform
from .pack import manifest_summary, print_json_summary, write_manifest
from .platforms.douyin import grab_douyin
from .platforms.weixin import grab_weixin
from .platforms.xhs import grab_xhs
from .utils import DEFAULT_OUT_ROOT, load_runtime_env

app = typer.Typer(add_completion=False, no_args_is_help=True)


async def grab_one(
    url: str,
    out_root: Path,
    no_transcript: bool,
    no_frames: bool,
    save_to_obsidian: bool,
) -> dict[str, object]:
    platform = detect_platform(url)
    if platform == "xhs":
        result = await grab_xhs(url, out_root)
    elif platform == "douyin":
        result = await grab_douyin(url, out_root)
    elif platform == "weixin":
        result = await grab_weixin(url, out_root)
    else:
        raise ValueError(f"Unsupported platform: {platform}")

    if result.video:
        await comprehend_video(result, no_transcript=no_transcript, no_frames=no_frames)

    manifest_path = write_manifest(result)
    summary = manifest_summary(result, manifest_path)
    if save_to_obsidian:
        summary["obsidian_path"] = await save_obsidian(result)
    print(str(manifest_path.resolve()))
    return summary


async def run(
    urls: tuple[str, ...],
    out: Path,
    no_transcript: bool,
    no_frames: bool,
    save_to_obsidian: bool,
    json_output: bool,
) -> None:
    load_runtime_env()
    summaries = []
    for url in urls:
        summaries.append(
            await grab_one(url, out.expanduser(), no_transcript, no_frames, save_to_obsidian)
        )
    if json_output:
        print_json_summary(summaries)


@app.command()
def main_cmd(
    urls: Annotated[list[str], typer.Argument(help="One or more XHS, Douyin, or WeChat URLs.")],
    save_obsidian: Annotated[
        bool, typer.Option("--save-obsidian", help="Also summarize and save to Obsidian.")
    ] = False,
    no_transcript: Annotated[
        bool, typer.Option("--no-transcript", help="Skip OpenAI Whisper transcription.")
    ] = False,
    no_frames: Annotated[
        bool, typer.Option("--no-frames", help="Skip ffmpeg frame extraction.")
    ] = False,
    out: Annotated[
        Path, typer.Option("--out", help="Context-pack output root.")
    ] = DEFAULT_OUT_ROOT,
    json_output: Annotated[
        bool, typer.Option("--json", help="Print a machine-readable manifest summary.")
    ] = False,
) -> None:
    asyncio.run(run(tuple(urls), out, no_transcript, no_frames, save_obsidian, json_output))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
