from __future__ import annotations

import time
from pathlib import Path

import httpx

from ..models import GrabResult
from ..pack import write_caption
from ..utils import id_from_url, safe_slug
from ._subprocess import require_engine, run_worker


def _video_urls(data: dict) -> list[str]:
    urls: list[str] = []
    video_data = data.get("video_data") or {}
    for key in ("nwm_video_url", "nwm_video_url_HQ", "wm_video_url", "wm_video_url_HQ"):
        if video_data.get(key):
            urls.append(str(video_data[key]))
    video = data.get("video") or {}
    play = video.get("play_addr") if isinstance(video, dict) else {}
    play_urls = play.get("url_list") if isinstance(play, dict) else None
    if play_urls:
        urls.extend(str(url) for url in play_urls)
    deduped = list(dict.fromkeys(urls))
    if not deduped:
        raise RuntimeError("Douyin result does not include a video URL")
    return deduped


async def grab_douyin(url: str, out_root: Path) -> GrabResult:
    engine_dir = require_engine("Douyin_TikTok_Download_API")
    data = run_worker(
        "grab.platforms._douyin_worker",
        engine_dir,
        {"url": url, "engine_dir": str(engine_dir)},
    )
    content_id = str(data.get("video_id") or data.get("aweme_id") or id_from_url(url, "douyin"))
    root = out_root / f"douyin_{safe_slug(content_id, fallback='douyin', limit=48)}"
    root.mkdir(parents=True, exist_ok=True)
    video_path = root / "video.mp4"
    direct_urls = _video_urls(data)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
            "Mobile/15E148 Safari/604.1"
        ),
        "Referer": "https://www.douyin.com/",
        "Range": "bytes=0-",
    }
    last_error = None
    async with httpx.AsyncClient(follow_redirects=True, timeout=90) as client:
        for direct_url in direct_urls:
            try:
                response = await client.get(direct_url, headers=headers)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                last_error = exc
                continue
            video_path.write_bytes(response.content)
            break
        else:
            raise RuntimeError(f"All Douyin video URLs failed: {last_error}") from last_error
    author = data.get("author") or {}
    nickname = author.get("nickname", "") if isinstance(author, dict) else ""
    created = data.get("create_time")
    publish_date = time.strftime("%Y-%m-%d", time.localtime(int(created))) if created else ""
    result = GrabResult(
        platform="抖音",
        source_url=url,
        content_id=content_id,
        title=str(data.get("desc") or content_id),
        author=nickname,
        publish_date=publish_date,
        content_type="视频",
        caption=str(data.get("desc") or ""),
        root=root,
        video=video_path,
        extra={"engine": "Douyin_TikTok_Download_API"},
    )
    write_caption(result)
    return result
