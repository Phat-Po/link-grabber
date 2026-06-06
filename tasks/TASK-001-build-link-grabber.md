# TASK-001 · 构建 link-grabber（全局内容理解工具）

> 给下一个执行 agent。本文档 **决策完整、可直接执行**。所有平台引擎、API 协议、
> prompt、样本链接、关键坑都已在 `_playground` 实测验证（见文末「参考资产」）。
> 执行前先读一遍全文，再按 Phase 1→5 顺序做。遇到与本文档冲突的现实情况，停下报告，不要擅自改设计。

---

## 0. 一句话目标
做一个统一 CLI `grab <url>` + 全局 Skill，让任意 project / 任意 agent 拿到
小红书 / 抖音 / 公众号链接（图文或视频）就能**抓取并理解内容**，再基于理解完成用户任务。

## 1. 背景与已定决策（不要重新讨论）
- **架构**：抽取内核 + 两消费者。
  - 用法B（默认）：`link → context-pack → 喂 agent 理解 → 干活`，**不存 Obsidian**。
  - 用法A（`--save-obsidian`）：额外跑 AI 分类摘要 + 写 Obsidian `WeChat/{分类}/`。
- **封装**：全局 Skill（`~/.claude/skills/link-grabber/`）+ 底层 CLI。
- **视频理解**：ffmpeg 抽关键帧（Claude 看画面）+ OpenAI Whisper API 转录（听语音）。
- **落点**：本正式 project（已建骨架）。引擎放 `engines/`，subprocess 隔离调用避免依赖打架。
- **微信归档目录**：`WeChat/{中文分类}/`，沿用 wechat-article-summary 扩展，AI 自动分类。
- **小红书新增需求（本次补充，重点）**：每篇作品**单独一个 folder**，folder 内除媒体外
  必须有一个 **markdown 文件保存标题 + 完整文案**（原本只下了图/视频，没存文字）。

## 2. 安全约束（硬性）
- 全程**无登录、不发送任何平台 Cookie**（账号零暴露 = 无可封账号）。
- 公众号抓取必须：住宅 IP（提示用户别开 VPN/数据中心 IP）、并发=1、每篇随机 15–40s 限速、
  命中「环境异常」立即停止退避。
- `.env`（含 OBSIDIAN_API_KEY）必须 gitignore（已配）。OPENAI_API_KEY 走环境变量，勿硬编码。
- 写 Obsidian 仅在 `--save-obsidian`，默认不碰真实库。
- `git push` 需用户确认（沿用工作区规则）。

---

## 3. 目标结构
```
20260605__tool__link-grabber/
├── pyproject.toml              # uv 项目，console_script: grab = grab.cli:main
├── src/grab/
│   ├── __init__.py
│   ├── cli.py                  # 入口与参数解析
│   ├── detect.py               # URL → 平台
│   ├── platforms/
│   │   ├── xhs.py              # 小红书：调 XHS-Downloader 引擎
│   │   ├── douyin.py           # 抖音：调 Douyin API 引擎
│   │   └── weixin.py           # 公众号：Playwright 抽取（搬 PoC）
│   ├── comprehend.py           # ffmpeg 关键帧 + Whisper 转录
│   ├── pack.py                 # 生成 context-pack + manifest.md
│   └── archive.py              # 用法A：AI 摘要 + 写 Obsidian（搬 PoC）
├── engines/
│   ├── XHS-Downloader/         # git clone（各自 venv，gitignore）
│   └── Douyin_TikTok_Download_API/
└── ~/.claude/skills/link-grabber/SKILL.md   # 全局 skill（不在本 repo 内）
```

---

## 4. 统一 CLI 规格
```
grab <url> [<url> ...] [选项]
选项：
  --save-obsidian      额外跑 AI 摘要并写 Obsidian WeChat/{分类}/（用法A）
  --no-transcript      视频跳过 Whisper 转录（省成本，只抽帧）
  --no-frames          视频跳过抽帧（只转录）
  --out <dir>          context-pack 输出根目录（默认 ~/.cache/link-grabber/）
  --json               额外打印机器可读的 manifest 摘要（给 agent 解析）
```
行为：判平台 → 派引擎下载 → 视频跑 comprehend → pack 生成 context-pack →
打印 `manifest.md` 绝对路径（agent 据此读取与看图）。多链接顺序处理。

### context-pack 产物（每条链接一个目录）
```
~/.cache/link-grabber/<platform>_<id>/
├── manifest.md         ← agent 读这个（聚合所有信息 + 看图指引）
├── caption.md          ← 标题 + 正文/文案（纯文本，必产）
├── images/ 1.jpg 2.jpg…
├── video.mp4           （视频作品）
├── frames/ frame_0001.jpg…   （抽帧）
└── transcript.txt      （Whisper 转录）
```

### manifest.md 格式（agent 入口，务必稳定）
```markdown
# [平台] 标题
- 作者：xxx ｜ 日期：xxx ｜ 来源：<url> ｜ 类型：图文/视频

## 文案 / 正文
<caption 或正文全文>

## 图片（请逐张查看，含图上文字）
- images/1.jpg
- images/2.jpg

## 视频关键帧（请查看理解画面）
- frames/frame_0001.jpg …

## 语音转录
<transcript 全文>

---
> agent 提示：请 Read 上面列出的图片/帧文件以理解视觉内容，结合文案/转录完成用户任务。
```

---

## 5. 平台适配规格（含实测要点）

### 5.1 小红书 `platforms/xhs.py`
- 引擎：`engines/XHS-Downloader`（JoeanAmier/XHS-Downloader，⭐11.4k，GPL-3.0）。
- 用 `uv sync` 装（`requires-python>=3.12`）。编程入口：`from source import XHS`，
  `async with XHS(...) as xhs: data = await xhs.extract(link, download=True)`。
- 参数要点（见 PoC）：`folder_mode=True`（**每篇独立 folder，满足新需求**）、
  `image_download=True`、`video_download=True`、`record_data=True`、`work_path` 指向 context-pack。
- `extract()` 返回列表，每项含 `作品标题`、`作品描述`、`作品类型`、`下载地址`。
- **新增必做**：下载后把 `作品标题` + `作品描述` 写成 `caption.md` 放进该篇 folder。
  （原本只落媒体，没存文字——这是本次用户明确补充的需求。）
- 支持 `xhslink.com/o/xxx` 口令短链直接传入（实测可用）。
- 图文无需 Cookie；**视频要原画高清需网页版 Cookie**（默认低清，文档里提示用户）。
- 实测样本：图文 `http://xhslink.com/o/3GATQJP3HgA`、视频 `http://xhslink.com/o/1ZGMIKHVZiA`。

### 5.2 抖音 `platforms/douyin.py`
- 引擎：`engines/Douyin_TikTok_Download_API`（Evil0ctal）。`requirements.txt` 装进独立 venv。
- 入口：`from crawlers.hybrid.hybrid_crawler import HybridCrawler`；
  `data = await HybridCrawler().hybrid_parsing_single_video(url, minimal=True)`。
- 视频直链：`data['video']['play_addr']['url_list'][0]`（实测拿到 1080p 无水印）。
  caption 在 `data['desc']`，作者 `data['author']['nickname']`。
- 用 httpx 跟随重定向下载 mp4 到 context-pack。支持 `v.douyin.com/xxx/` 短链。
- 实测样本：`https://v.douyin.com/16opyW1Vvmo/`（jisoo 舞台直拍，1080p 17MB 成功）。

### 5.3 公众号 `platforms/weixin.py`
- **直接搬 PoC**：`_playground/scratch/20260605-wechat-batch-obsidian/wx_batch.py` 的
  Playwright 抽取逻辑（`EXTRACT_JS` + `fetch_one`），已处理两种格式：
  - 旧版 rich_media 文章 → `#js_content`（实测 Datawhale 文 6551 字完整）
  - 新版「图片消息」`share_content_page` → 正文在 `#js_image_desc`，图在轮播 swiper
    （`#img_swiper_content img` / `.share_media_swiper_content img`，取 data-src）。
    ⚠️ 新版的 `#js_content` 是**赞赏UI垃圾**，必须先判 `#js_image_desc`。
- **坑**：`og:description` 带 `\x0a \x26amp;` JS 转义垃圾，**优先用 `#js_image_desc.innerText`**
  干净文本，仅其为空时才退回 og:description。
- **坑**：数据中心 IP / VPN 出口会被风控「环境异常」拦截；**住宅 IP 无 Cookie 即 HTTP 200**。
- 标题 `#activity-name`/`.rich_media_title`；作者 `#js_name`/`.account_nickname_inner`；
  日期 `#publish_time`（图片帖是相对时间「2小时前」，退回当天日期即可，用户已说绝对日期「不用」做）。
- ⚠️ 顺带发现：现有 wechat-article-summary 扩展只认旧版 `#js_content`，遇新版图片帖抓不到；
  本工具的双格式抽取顺带补了这个短板（已在扩展 STATUS 记录）。

---

## 6. 理解层 `comprehend.py`
- **关键帧**：`ffmpeg -i video.mp4 -vf fps=1/FRAME_INTERVAL_SEC frames/frame_%04d.jpg`，
  上限 `FRAME_MAX` 帧（默认每 4s 一帧、最多 40 帧）。ffmpeg 8.0 已就位。
- **转录**：本机无 whisper，用 OpenAI Whisper API（`whisper-1`，环境 `OPENAI_API_KEY`）。
  长视频先用 ffmpeg 抽音轨为 mp3/m4a 再传。`--no-transcript` 可跳过。
- 成本提示：Whisper 按时长计费（约 $0.006/分钟），写进 README 与 skill 说明。

## 7. 存档层 `archive.py`（用法A，可选）
- **直接搬 PoC** 的 `summarize()` + `obsidian_put()` + `build_note()`
  （`_playground/scratch/20260605-wechat-batch-obsidian/wx_batch.py`）。
- AI prompt 必须与扩展 `lib/openai.js` 完全一致（PoC 已复刻）：分类用固定中文类目，
  默认「其他」；返回 one_line_summary / key_points / category / tags / reading_value /
  reading_time_min / read_mode / is_clickbait / honest_title。
- note 格式与扩展 `lib/obsidian.js` `buildNote` 完全一致（frontmatter + 要点 + 原文 + 笔记）。
- Obsidian 写入：`PUT http://127.0.0.1:27123/vault/{urlencoded path}`，`Bearer {OBSIDIAN_API_KEY}`，
  `Content-Type: text/markdown`，同名去重 `_2.._50`。实测 key 与协议有效。
- 小红书/抖音用 `--save-obsidian` 时也可走存档（分类可用「其他」或加平台标签），但优先保证用法B。

---

## 8. 全局 Skill `~/.claude/skills/link-grabber/SKILL.md`
- **触发**：用户在任意 project 给出小红书/抖音/公众号链接，要求 agent「参考/理解/学习」
  这些内容来完成某任务（写小红书图文、做方案、模仿风格等）。典型 1–5 条链接。
- **动作**：
  1. 对每条 link 跑 `uv run grab "<url>"`（或装好的 `grab`），拿到 manifest.md 路径。
  2. Read manifest.md + Read 其中列出的图片/帧文件（多模态理解视觉内容）。
  3. 综合文案/正文 + 视觉 + 转录，**理解内容**，再执行用户的真实任务。
- **说明**：内置公众号住宅 IP 提示、无登录安全说明、Whisper 成本提示、`--save-obsidian` 用法。
- SKILL.md 写法参考工作区现有 skills 风格（name/description frontmatter + 步骤）。

---

## 9. 依赖策略
- 本 repo 主 venv：playwright、httpx、markdownify、beautifulsoup4、（cli）click/typer。
- 两个三方引擎**各自独立 venv**（`engines/*/`），通过 subprocess 或独立 `uv run` 调用，
  避免与主项目依赖冲突。`engines/` 已在 .gitignore（clone 在 setup 阶段做）。
- `playwright install chromium` 需跑一次（PoC 已下过，缓存在 `~/Library/Caches/ms-playwright`）。

## 10. 验收清单（用实测样本全平台跑通）
- [ ] 小红书图文：`http://xhslink.com/o/3GATQJP3HgA` → 独立 folder + 图 + **caption.md（标题+文案）** + manifest
- [ ] 小红书视频：`http://xhslink.com/o/1ZGMIKHVZiA` → 视频 + 帧 + 转录 + caption.md
- [ ] 抖音视频：`https://v.douyin.com/16opyW1Vvmo/` → 1080p mp4 + 帧 + 转录 + desc
- [ ] 公众号文章：`https://mp.weixin.qq.com/s/Oo0iksfTXvUSFNnBrWOOpw` → 正文 md + manifest
- [ ] 公众号图片帖：`https://mp.weixin.qq.com/s/HzXa5eyNBFIHQGiWktGOsA` → 文案 + 图 + manifest
- [ ] `--save-obsidian` 跑公众号 → 写进 `WeChat/{AI分类}/`，格式同扩展
- [ ] Skill：在另一个 project 里贴 1 条链接，agent 自动调 grab + 看图 + 完成一个示例任务
- [ ] 安全：确认无任何登录态/ Cookie；公众号限速生效

## 11. 待办 / 未来（非本次必须）
- 批量从 `links.txt` 读入（用户当前用 1–5 条手动，暂不急）
- 小红书视频高清需 Cookie 的可选配置
- 图片帖绝对发布时间（用户说「不用」，保持退回当天）
- 把存档层与 wechat-article-summary 扩展打通成统一后端（远期）

---

## 12. 参考资产（已验证，直接复用，别重造）
| 内容 | 位置 |
|------|------|
| 公众号抽取+AI摘要+Obsidian 全套 PoC 代码 | `_playground/scratch/20260605-wechat-batch-obsidian/wx_batch.py` |
| 小红书引擎（已 clone + sync） | `_playground/scratch/20260605-xhs-downloader-test/XHS-Downloader` |
| 抖音引擎（已 clone + venv） | `_playground/scratch/20260605-xhs-downloader-test/douyin-api` |
| 扩展 AI prompt（分类/评分规则） | `20260324__extension__wechat-article-summary/lib/openai.js` |
| 扩展 note 格式 + Obsidian 协议 | `20260324__extension__wechat-article-summary/lib/obsidian.js` |
| 实验全过程记录 | `_playground/LOG.md`（2026-06-05 多条） |

**环境事实**：ffmpeg 8.0.1 在；无本地 whisper（用 API）；环境有可用 `OPENAI_API_KEY`(真OpenAI gpt-4o-mini)；
Obsidian Local REST API 在 HTTP **27123**（非 27124），key 在本项目 `.env`；活跃归档目录 `WeChat/`（17 中文分类子目录）。
