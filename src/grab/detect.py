from __future__ import annotations

from urllib.parse import urlparse


class UnsupportedPlatformError(ValueError):
    pass


def detect_platform(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "xiaohongshu.com" in host or "xhslink.com" in host:
        return "xhs"
    if "douyin.com" in host:
        return "douyin"
    if "mp.weixin.qq.com" in host or "weixin.qq.com" in host:
        return "weixin"
    raise UnsupportedPlatformError(f"Unsupported platform for URL: {url}")
