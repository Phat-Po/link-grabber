from __future__ import annotations

import json
import os
import re
import urllib.parse
from datetime import datetime

import httpx

from .models import GrabResult
from .utils import safe_slug

AI_SYSTEM_PROMPT = """你是一个中文文章摘要助手。根据提供的微信公众号文章内容，输出结构化的 JSON 摘要。

要求：
1. one_line_summary: 用一句话概括文章核心观点，不超过30字。不要写"本文讨论了..."这种废话，直接说结论。
2. key_points: 提取3-5个核心要点，每条不超过50字。是文章的观点和结论，不是章节标题。
3. category: 从以下列表中选择最匹配的一个分类：科技、商业、金融、政治、教育、健康、文化、生活、职场、创业、设计、法律、心理、其他
4. tags: 提取2-3个具体的话题标签。要求是具体的名词或短语（如"AI监管""新能源车"），不是抽象词（如"深度思考""行业洞察"）。
5. reading_value: 根据信息密度和参考价值评分1-5分，规则如下：
   - 1分：纯营销软文/广告、情绪煽动无实质内容、极短碎片（<300字）
   - 2分：资讯转述为主，无原创分析；热点跟风、列表堆砌但无深度
   - 3分：有一定观点但论证薄弱，或仅有一两个实用信息点；适合快速扫一眼
   - 4分：有原创分析或一手经验，论点有支撑，读完有具体可操作收获
   - 5分：高密度干货，数据/案例/框架/方法论齐全，逻辑严密，读完能直接应用
   - 注意：标题是否标题党不影响评分，评分只看内容本身质量
6. reading_time_min: 根据文章长度估算阅读时间（分钟）。
7. read_mode: 根据文章阅读负担输出 "light" 或 "deep"。
   - light：轻量快读，信息结构简单，适合几分钟内扫完
   - deep：需要更高专注度，信息密度高、论证更长，或需要完整读完才有收获
   - 注意：优先看实际阅读负担，不要只按标题或主题判断
8. is_clickbait: 仅当标题存在以下明显情形时才标为true，否则为false（宁可漏标，不要误标）：
   - 标题用模糊/神秘措辞吊胃口，让读者不读完就不知道说的是什么（如"一个比一个魔怔""你绝对想不到"）
   - 标题暗示重大揭秘或颠覆性结论，内容却是常识或普通资讯
   - 标题主题与文章实际内容存在明显落差或误导
   - 注意：措辞生动、有观点、情绪化、用比喻≠标题党，只要内容能承接标题就不算
9. honest_title: 仅当 is_clickbait 为 true 时，用一句话直接说清楚"读完这篇文章你会知道什么"——完整回答标题暗示的那个问题，要具体说出人物/事件/结论，不要只解释标题中某个词的字面意思。例如：标题"韩国人的咖啡病，中国人来治愈？"→ 应写"霸王茶姬等中国茶饮品牌借助KPop营销进军韩国，试图在咖啡主导市场中争夺消费者"，而不是"韩国人对咖啡依赖过度"。is_clickbait 为 false 时输出 null。

输出格式：纯 JSON，不要 markdown 代码块。"""


async def summarize(result: GrabResult) -> dict:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required for --save-obsidian")
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    content = (result.caption or "")[:8000]
    user = (
        f"标题：{result.title}\n作者：{result.author or '未知'}\n"
        f"发布时间：{result.publish_date or '未知'}\n\n{content}"
    )
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "temperature": 0.3,
                "max_tokens": 800,
                "messages": [
                    {"role": "system", "content": AI_SYSTEM_PROMPT},
                    {"role": "user", "content": user},
                ],
            },
        )
    response.raise_for_status()
    text = response.json()["choices"][0]["message"]["content"]
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise RuntimeError(f"OpenAI returned no JSON: {text[:120]}")
    return json.loads(match.group(0))


def build_note(result: GrabResult, summary: dict) -> str:
    esc_title = (result.title or "").replace('"', '\\"')
    esc_author = (result.author or "").replace('"', '\\"')
    tags = ", ".join(f'"{tag}"' for tag in summary.get("tags", []))
    key_points = "\n".join(f"- {point}" for point in summary.get("key_points", []))
    created = datetime.now().astimezone().isoformat()
    return f"""---
title: "{esc_title}"
author: "{esc_author}"
date: "{result.publish_date or ""}"
source: "{result.source_url}"
category: "{summary.get("category", "其他")}"
tags: [{tags}]
rating: {summary.get("reading_value", 0)}
reading_time: {summary.get("reading_time_min", 0)}
read: false
created: "{created}"
ai_summary: true
---

# {result.title or "（无标题）"}

**{summary.get("one_line_summary", "")}**

## 要点

{key_points or "- （无摘要）"}

---

## 原文

{result.caption or ""}

## 笔记

"""


async def obsidian_put(file_path: str, body: str) -> str:
    key = os.getenv("OBSIDIAN_API_KEY")
    if not key:
        raise RuntimeError("OBSIDIAN_API_KEY is required for --save-obsidian")
    host = os.getenv("OBSIDIAN_HOST", "127.0.0.1")
    port = os.getenv("OBSIDIAN_PORT", "27123")
    base = f"http://{host}:{port}/vault/"
    headers = {"Authorization": f"Bearer {key}"}
    stem, ext = file_path.rsplit(".", 1)
    async with httpx.AsyncClient(timeout=20) as client:
        chosen = file_path
        for index in range(1, 51):
            candidate = file_path if index == 1 else f"{stem}_{index}.{ext}"
            url = base + "/".join(urllib.parse.quote(part) for part in candidate.split("/"))
            probe = await client.get(url, headers=headers)
            if probe.status_code == 404:
                chosen = candidate
                break
            if probe.status_code == 401:
                raise RuntimeError("Obsidian API key rejected")
        else:
            raise RuntimeError("Obsidian 同名文件过多")
        url = base + "/".join(urllib.parse.quote(part) for part in chosen.split("/"))
        put = await client.put(
            url,
            headers={**headers, "Content-Type": "text/markdown"},
            content=body.encode("utf-8"),
        )
        put.raise_for_status()
    return chosen


async def save_obsidian(result: GrabResult) -> str:
    summary = await summarize(result)
    category = summary.get("category") or "其他"
    date = result.publish_date or datetime.now().date().isoformat()
    title = safe_slug(result.title, fallback=result.content_id, limit=40)
    prefix = os.getenv("VAULT_PREFIX", "WeChat/").rstrip("/") + "/"
    file_path = f"{prefix}{category}/{date}_{title}.md"
    return await obsidian_put(file_path, build_note(result, summary))
