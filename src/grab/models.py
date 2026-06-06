from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GrabResult:
    platform: str
    source_url: str
    content_id: str
    title: str = ""
    author: str = ""
    publish_date: str = ""
    content_type: str = "unknown"
    caption: str = ""
    root: Path | None = None
    images: list[Path] = field(default_factory=list)
    video: Path | None = None
    frames: list[Path] = field(default_factory=list)
    transcript: Path | None = None
    extra: dict[str, str | int | float | bool | None] = field(default_factory=dict)

    @property
    def safe_title(self) -> str:
        return self.title or self.content_id or "untitled"
