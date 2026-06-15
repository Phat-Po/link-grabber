from __future__ import annotations

import re
from pathlib import Path

import httpx
from markdownify import markdownify as md
from playwright.async_api import async_playwright

from ..models import GrabResult
from ..pack import write_caption
from ..utils import id_from_url, norm_date, safe_slug


UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15"
)

REMOVE_SELECTORS = [
    ".qr_code_pc_outer",
    "#js_pc_qr_code",
    ".rich_media_tool",
    ".wx_follow_tip",
    "#js_msg_card",
    "#js_profile_qrcode",
    "mpvoice",
    "mp-miniprogram",
    ".js_wx_tap_highlight",
    ".share_notice",
]

EXTRACT_JS = r"""(removeSelectors) => {
    const bodyText = document.body ? document.body.innerText : '';
    if (/环境异常|完成验证后即可继续访问/.test(bodyText) && bodyText.length < 400) {
        return { block: true };
    }
    const metaDesc = (document.querySelector('meta[property="og:description"]')||{}).content || '';
    const titleEl = document.querySelector('#activity-name') ||
                    document.querySelector('.rich_media_title') ||
                    document.querySelector('h1');
    const title = (titleEl ? titleEl.textContent : document.title).trim();
    const authorEl = document.querySelector('#js_name') ||
                     document.querySelector('.account_nickname_inner') ||
                     document.querySelector('.wx_follow_nickname');
    const author = authorEl ? authorEl.textContent.trim() : '';
    const dateEl = document.querySelector('#publish_time');
    const date = dateEl ? dateEl.textContent.trim() : '';

    const imgDesc = document.querySelector('#js_image_desc');
    if (imgDesc) {
        const seen = new Set();
        const imgs = [];
        document.querySelectorAll(
            '#img_swiper_content img, .share_media_swiper_content img, .swiper_item img'
        ).forEach(img => {
            const real = img.dataset.src || img.getAttribute('data-src') || img.src;
            if (real && !real.startsWith('data:') && !seen.has(real)) { seen.add(real); imgs.push(real); }
        });
        let text = (imgDesc.innerText || '').trim();
        if (!text) text = metaDesc;
        const imgMd = imgs.map(u => `![](${u})`).join('\n\n');
        const html = (imgMd ? imgMd + '\n\n' : '') +
                     text.split(/\n+/).map(l => l.trim()).filter(Boolean).map(l => `<p>${l}</p>`).join('');
        return { ok: true, type: 'image_post', title, author, date, html, images: imgs };
    }

    const contentEl = document.querySelector('#js_content') ||
                      document.querySelector('.rich_media_content');
    if (!contentEl) return { ok: false, reason: 'no_content_el' };
    const clone = contentEl.cloneNode(true);
    const imgs = [];
    clone.querySelectorAll('img').forEach(img => {
        const real = img.dataset.src || img.dataset.lazySrc || img.getAttribute('data-lazysrc') || img.src;
        if (real && !real.startsWith('data:')) {
            img.setAttribute('src', real);
            imgs.push(real);
        }
    });
    removeSelectors.forEach(sel => {
        try { clone.querySelectorAll(sel).forEach(el => el.remove()); } catch(e){}
    });
    return { ok: true, type: 'article', title, author, date, html: clone.innerHTML, images: imgs };
}"""


async def _fetch_article(url: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=UA, viewport={"width": 414, "height": 896}, locale="zh-CN"
        )
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=45000)
            await page.wait_for_timeout(2500)
            res = await page.evaluate(EXTRACT_JS, REMOVE_SELECTORS)
        finally:
            await browser.close()
    if res.get("block"):
        raise RuntimeError("命中微信风控（环境异常）—— 建议关闭 VPN/换住宅 IP 后再试")
    if not res.get("ok"):
        raise RuntimeError(f"未找到正文容器 ({res.get('reason')})")
    content_md = md(res["html"], heading_style="ATX", bullets="-").strip()
    content_md = re.sub(r"\n{3,}", "\n\n", content_md)
    return {
        "title": res["title"],
        "author": res["author"],
        "publishDate": norm_date(res["date"]),
        "raw_date": res["date"],
        "content": content_md,
        "url": url,
        "type": res.get("type", "article"),
        "images": res.get("images") or [],
    }


async def _download_images(urls: list[str], root: Path) -> list[Path]:
    image_dir = root / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        for index, url in enumerate(urls, start=1):
            suffix = ".jpg"
            clean = url.split("?", 1)[0].lower()
            for candidate in (".png", ".webp", ".jpeg", ".jpg", ".gif"):
                if clean.endswith(candidate):
                    suffix = candidate
                    break
            path = image_dir / f"{index}{suffix}"
            try:
                response = await client.get(
                    url, headers={"User-Agent": UA, "Referer": "https://mp.weixin.qq.com/"}
                )
                response.raise_for_status()
            except httpx.HTTPError:
                continue
            path.write_bytes(response.content)
            paths.append(path)
    return paths


async def grab_weixin(url: str, out_root: Path) -> GrabResult:
    article = await _fetch_article(url)
    content_id = id_from_url(url, "weixin")
    root = out_root / f"weixin_{safe_slug(content_id, fallback='weixin', limit=48)}"
    root.mkdir(parents=True, exist_ok=True)
    images = await _download_images(article["images"], root)
    result = GrabResult(
        platform="微信公众号",
        source_url=url,
        content_id=content_id,
        title=article["title"],
        author=article["author"],
        publish_date=article["publishDate"],
        content_type="图片帖" if article["type"] == "image_post" else "文章",
        caption=article["content"],
        root=root,
        images=images,
        extra={"raw_date": article["raw_date"]},
    )
    write_caption(result)
    return result
