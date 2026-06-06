from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path


async def main() -> None:
    payload = json.loads(sys.argv[1])
    engine_dir = Path(payload["engine_dir"]).resolve()
    if str(engine_dir) not in sys.path:
        sys.path.insert(0, str(engine_dir))

    from source import XHS

    async with XHS(
        work_path=payload["work_path"],
        folder_name=".",
        record_data=True,
        image_download=True,
        video_download=True,
        live_download=False,
        download_record=False,
        folder_mode=True,
        language="zh_CN",
    ) as xhs:
        data = await xhs.extract(payload["url"], download=True)
    print(json.dumps(data or [], ensure_ascii=False, default=str))


if __name__ == "__main__":
    asyncio.run(main())
