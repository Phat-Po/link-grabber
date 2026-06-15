from __future__ import annotations

import shutil
from pathlib import Path

from ..models import GrabResult
from ..pack import write_caption
from ..utils import id_from_url, safe_slug
from ._subprocess import require_engine, run_worker


def _collect_media(root: Path) -> tuple[list[Path], Path | None]:
    images = sorted(
        p
        for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".heic"}
    )
    videos = sorted(
        p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".mp4", ".mov"}
    )
    video = videos[0] if videos else None
    return images, video


def _find_item_folder(base: Path, before: set[Path]) -> Path:
    candidates = [p for p in base.rglob("*") if p.is_dir() and p not in before]
    if not candidates:
        return base
    media_dirs = []
    for folder in candidates:
        images, video = _collect_media(folder)
        if images or video:
            media_dirs.append(folder)
    if media_dirs:
        return sorted(media_dirs, key=lambda p: len(p.parts))[-1]
    return sorted(candidates, key=lambda p: len(p.parts))[-1]


async def grab_xhs(url: str, out_root: Path) -> GrabResult:
    engine_dir = require_engine("XHS-Downloader")
    content_id = id_from_url(url, "xhs")
    scratch = out_root / f"xhs_{content_id}_raw"
    scratch.mkdir(parents=True, exist_ok=True)
    before = {p for p in scratch.rglob("*") if p.is_dir()}
    data = run_worker(
        "grab.platforms._xhs_worker",
        engine_dir,
        {"url": url, "work_path": str(scratch), "engine_dir": str(engine_dir)},
    )
    if not data:
        raise RuntimeError("XHS engine returned an empty result")
    item = data[0]
    desc = item.get("作品描述") or item.get("desc") or ""
    title = item.get("作品标题") or item.get("title") or ""
    if not title or str(title).strip().lower() == "xhs":
        title = str(desc).strip().splitlines()[0] if str(desc).strip() else "xhs"
    work_id = item.get("作品ID") or item.get("note_id") or content_id
    final_root = out_root / f"xhs_{safe_slug(str(work_id), fallback=content_id, limit=48)}"
    item_folder = _find_item_folder(scratch, before)
    if item_folder != final_root:
        if final_root.exists():
            for child in item_folder.iterdir():
                target = final_root / child.name
                if child.is_dir():
                    shutil.copytree(child, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(child, target)
        else:
            final_root.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(item_folder), str(final_root))
    final_root.mkdir(parents=True, exist_ok=True)
    images, video = _collect_media(final_root)
    result = GrabResult(
        platform="小红书",
        source_url=url,
        content_id=str(work_id),
        title=str(title),
        author=str(item.get("作者昵称") or item.get("nickname") or ""),
        publish_date=str(item.get("发布时间") or ""),
        content_type=str(item.get("作品类型") or ("视频" if video else "图文")),
        caption=str(desc),
        root=final_root,
        images=images,
        video=video,
        extra={"engine": "XHS-Downloader"},
    )
    write_caption(result)
    return result
