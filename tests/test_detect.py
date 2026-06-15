from __future__ import annotations

import pytest

from grab.detect import UnsupportedPlatformError, detect_platform


class TestDetectPlatform:
    def test_xhs_xiaohongshu(self):
        assert detect_platform("https://www.xiaohongshu.com/explore/abc123") == "xhs"

    def test_xhs_xhslink(self):
        assert detect_platform("http://xhslink.com/o/3GATQJP3HgA") == "xhs"

    def test_douyin(self):
        assert detect_platform("https://v.douyin.com/16opyW1Vvmo/") == "douyin"

    def test_weixin(self):
        assert detect_platform("https://mp.weixin.qq.com/s/Oo0iksfTXvUSFNnBrWOOpw") == "weixin"

    def test_unsupported(self):
        with pytest.raises(UnsupportedPlatformError):
            detect_platform("https://www.google.com")

    def test_unsupported_youtube(self):
        with pytest.raises(UnsupportedPlatformError):
            detect_platform("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
