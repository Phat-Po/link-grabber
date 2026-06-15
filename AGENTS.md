# link-grabber — Project Governance

## Scope
全局「内容理解层」工具。给任意 agent / 任意 project 一个内容链接（小红书 / 抖音 / 微信公众号，图文或视频），自动抓取并转成 **agent 可直接读懂的形态**（文字 + 可看的图 + 视频关键帧 + 语音转录），喂进对话，让 agent 基于理解去完成用户的任务。

**一句话**：`link → 内容 → agent 看懂 → 干活`。

## What This Is / Is NOT
- ✅ 是：统一抽取 CLI（`grab <url>`）+ 全局 Skill（`~/.claude/skills/link-grabber/`），三平台内容 → context-pack
- ✅ 是：可选把内容存档进 Obsidian（`--save-obsidian`，复用 wechat-article-summary 的格式与库）
- ❌ 不是：wechat-article-summary 那个 Chrome 扩展的替代。扩展是浏览器内**人工逐篇存档**；本工具是 CLI/agent 的**程序化批量理解**。两者共享格式，用途不同。
- ❌ 不是：登录态爬虫。全程无登录、不发平台 Cookie。

## Two Consumers, One Core（核心设计）
```
        抽取内核 (src/grab/platforms/*)
  link → 本地内容(图·视频·文字)
            │
   ┌────────┴─────────┐
 用法B(默认)        用法A(--save-obsidian)
 context-pack→agent  AI摘要+写 WeChat/{分类}/
 "现在理解去干活"     "存档以后看"
```

## Stack
- Python 3.12 · uv
- Playwright(chromium) — 微信渲染抽取
- ffmpeg — 视频关键帧
- OpenAI API — Whisper 转录 + （存档时）摘要分类。复用环境变量 `OPENAI_API_KEY`
- 引擎：JoeanAmier/XHS-Downloader、Evil0ctal/Douyin_TikTok_Download_API（engines/，subprocess 隔离）

## Risk Gates（沿用工作区全局）
- `git push` / 部署 — 先确认
- 写 Obsidian 仅在 `--save-obsidian`，默认不碰
- 公众号抓取：住宅 IP、无登录、并发1、随机限速；命中风控即停
- `.env`（含 OBSIDIAN_API_KEY）必须 gitignore

## Layout
```
src/grab/        统一 CLI 与平台适配
engines/         三方抽取引擎（各自 venv）
tasks/           规划与执行文档
~/.claude/skills/link-grabber/   全局 skill（独立于本 repo，由 task doc 指定创建）
```

## Status
🟢 MVP 已实现并开源发布。GitHub: [Phat-Po/link-grabber](https://github.com/Phat-Po/link-grabber)
