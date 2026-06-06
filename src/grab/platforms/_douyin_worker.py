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
    from crawlers.hybrid.hybrid_crawler import HybridCrawler

    data = await HybridCrawler().hybrid_parsing_single_video(payload["url"], minimal=True)
    print(json.dumps(data or {}, ensure_ascii=False, default=str))


if __name__ == "__main__":
    asyncio.run(main())
