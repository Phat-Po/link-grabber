from __future__ import annotations

import json
from pathlib import Path

from .models import GrabResult
from .utils import rel_list


def write_caption(result: GrabResult) -> Path:
    if result.root is None:
        raise ValueError("result.root is required")
    result.root.mkdir(parents=True, exist_ok=True)
    path = result.root / "caption.md"
    title = result.title or "Untitled"
    body = result.caption or ""
    path.write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")
    return path


def write_manifest(result: GrabResult) -> Path:
    if result.root is None:
        raise ValueError("result.root is required")
    result.root.mkdir(parents=True, exist_ok=True)
    write_caption(result)
    image_lines = "\n".join(f"- {p}" for p in rel_list(result.images, result.root)) or "- （无）"
    frame_lines = "\n".join(f"- {p}" for p in rel_list(result.frames, result.root)) or "- （无）"
    transcript = ""
    if result.transcript and result.transcript.exists():
        transcript = result.transcript.read_text(encoding="utf-8").strip()
    transcript = transcript or "（无）"
    caption = (result.caption or "").strip() or "（无）"
    title = result.title or "Untitled"
    manifest = f"""# [{result.platform}] {title}
- 作者：{result.author or "未知"} ｜ 日期：{result.publish_date or "未知"} ｜ 来源：{result.source_url} ｜ 类型：{result.content_type}

## 文案 / 正文
{caption}

## 图片（请逐张查看，含图上文字）
{image_lines}

## 视频关键帧（请查看理解画面）
{frame_lines}

## 语音转录
{transcript}

---
> agent 提示：请 Read 上面列出的图片/帧文件以理解视觉内容，结合文案/转录完成用户任务。
"""
    path = result.root / "manifest.md"
    path.write_text(manifest, encoding="utf-8")
    return path


def manifest_summary(result: GrabResult, manifest_path: Path) -> dict[str, object]:
    return {
        "platform": result.platform,
        "id": result.content_id,
        "title": result.title,
        "author": result.author,
        "date": result.publish_date,
        "type": result.content_type,
        "manifest": str(manifest_path.resolve()),
        "root": str(result.root.resolve()) if result.root else "",
        "images": rel_list(result.images, result.root) if result.root else [],
        "frames": rel_list(result.frames, result.root) if result.root else [],
        "video": result.video.name if result.video else "",
        "transcript": result.transcript.name if result.transcript else "",
    }


def print_json_summary(summaries: list[dict[str, object]]) -> None:
    print(json.dumps(summaries, ensure_ascii=False, indent=2))
