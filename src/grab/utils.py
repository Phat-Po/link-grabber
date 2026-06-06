from __future__ import annotations

import os
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_ROOT = Path.home() / ".cache" / "link-grabber"


def load_runtime_env() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv()


def safe_slug(value: str | None, fallback: str = "untitled", limit: int = 80) -> str:
    text = value or fallback
    text = re.sub(r"[\\/:*?\"<>|#%&{}]", "_", text)
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"_+", "_", text).strip("._ ")
    return (text[:limit].strip("._ ") or fallback).lower()


def norm_date(raw: str | None) -> str:
    if raw:
        match = re.search(r"(\d{4})[^\d](\d{1,2})[^\d](\d{1,2})", raw)
        if match:
            return f"{match[1]}-{int(match[2]):02d}-{int(match[3]):02d}"
    return date.today().isoformat()


def id_from_url(url: str, fallback: str = "item") -> str:
    parsed = urlparse(url)
    tail = parsed.path.rstrip("/").split("/")[-1]
    if tail:
        return safe_slug(tail, fallback=fallback, limit=48)
    return safe_slug(parsed.netloc, fallback=fallback, limit=48)


def rel_list(paths: list[Path], root: Path) -> list[str]:
    values = []
    for path in paths:
        try:
            values.append(path.relative_to(root).as_posix())
        except ValueError:
            values.append(path.as_posix())
    return values


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}
