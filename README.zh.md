# link-grabber 🔗

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

**把社媒链接变成 AI agent 能直接读懂的 context pack。**

小红书 · 抖音 · 微信公众号 — 一个 CLI，三个平台，任意 agent。

📖 [English Documentation](README.md)

![hero](./marketing/screenshots/01-hero.png)

## 为什么需要 link-grabber？

你的 AI agent 读不了链接。把抖音视频 URL 贴给 Claude、ChatGPT 或任何 agent，它什么都看不到。你只能手动复制文字、截图、总结视频，再喂回去。

**link-grabber 自动完成整个流程。** 一条命令抽取文字、图片、视频关键帧、语音转录，输出结构化的 context pack，agent 直接消费。

<!-- SCREENSHOT: 02-pain.png -->

### 和竞品有什么不同

| 功能 | link-grabber | MediaCrawler | wechat-article-to-markdown | MarkItDown |
|------|:---:|:---:|:---:|:---:|
| 三平台（小红书 + 抖音 + 微信） | ✅ | ✅ | ❌ 仅微信 | ❌ 通用网页 |
| LLM-ready Markdown 输出 | ✅ | ❌ CSV/JSON | ✅ | ✅ |
| 视频关键帧抽取 | ✅ | ❌ | ❌ | ❌ |
| 语音转录（Whisper） | ✅ | ❌ | ❌ | ✅（音频文件） |
| 统一 context pack | ✅ | ❌ | ❌ | ❌ |
| AI agent 集成（Skill） | ✅ | ❌ | ✅ | ❌ |

<!-- SCREENSHOT: 03-platforms.png -->

## ✨ 特性

- 📕 **小红书** — 图文笔记 + 视频，通过 XHS-Downloader 引擎抽取
- 🎵 **抖音** — 视频关键帧 + Whisper 语音转录，通过 Douyin API 引擎
- 💬 **微信公众号** — Playwright 渲染抽取，支持新旧两版图文格式
- 🎬 **视频理解** — ffmpeg 抽取关键帧 + OpenAI Whisper 转录，10 分钟视频 → 2 分钟掌握
- 📦 **Context Pack** — `manifest.md` + 图片 + 视频帧 + 转录文本，agent 直接读取
- 📝 **Obsidian 存档**（可选）— `--save-obsidian` 自动 AI 分类摘要写入 Obsidian
- 🔒 **无登录** — 全程不发送平台 Cookie，公众号使用住宅 IP 限速

## 📋 环境要求

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)（包管理器）
- [ffmpeg](https://ffmpeg.org/)（视频帧抽取）
- [OpenAI API key](https://platform.openai.com/)（Whisper 转录，可用 `--no-transcript` 跳过）

## 📦 安装

```bash
git clone https://github.com/Phat-Po/link-grabber.git
cd link-grabber
uv sync
uv run playwright install chromium
```

## 🚀 快速上手

```bash
# 抓取小红书笔记
uv run grab "http://xhslink.com/o/3GATQJP3HgA"

# 抓取抖音视频（跳过转录节省成本）
uv run grab "https://v.douyin.com/16opyW1Vvmo/" --no-transcript

# 抓取微信公众号文章
uv run grab "https://mp.weixin.qq.com/s/Oo0iksfTXvUSFNnBrWOOpw"

# JSON 输出（用于管道）
uv run grab "<url>" --json
```

<!-- SCREENSHOT: 04-how.png -->

## 📦 输出结构

每次抓取在 `~/.cache/link-grabber/<platform>_<id>/` 生成一个 **context pack**：

```
xhs_3gatqjp3hga/
├── manifest.md          # 结构化摘要（agent 先读这个）
├── caption.md           # 原始标题 + 描述
├── 01.jpg               # 抽取的图片
├── 02.jpg
├── frame_001.jpg        # 视频关键帧（如果是视频）
├── frame_002.jpg
└── transcript.txt       # Whisper 转录（如果是视频 + 有 API key）
```

Agent 应先读 `manifest.md`，再查看其中列出的图片和视频帧。

## ⌨️ CLI 选项

```
uv run grab <urls...> [选项]

参数:
  urls               一个或多个小红书 / 抖音 / 微信公众号 URL

选项:
  --no-transcript    跳过 Whisper 转录（节省 API 费用）
  --no-frames        跳过 ffmpeg 帧抽取
  --save-obsidian    同时摘要并存档到 Obsidian
  --out PATH         自定义输出目录
  --json             输出机器可读的 manifest 摘要
```

## 🔧 配置

复制 `.env.example` 为 `.env` 并填写：

```bash
# 视频转录必需
OPENAI_API_KEY=sk-xxx

# 可选：Obsidian 存档（仅 --save-obsidian 时需要）
OBSIDIAN_API_KEY=xxx
OBSIDIAN_PORT=27123

# 可选：模型覆盖
OPENAI_MODEL=gpt-4o-mini
WHISPER_MODEL=whisper-1
```

<!-- SCREENSHOT: 05-quickstart.png -->

## 🛠️ 常见问题

**Playwright 安装失败：**
```bash
uv run playwright install chromium --with-deps
```

**找不到 ffmpeg：**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

**微信「环境异常」错误：**
微信可能拦截自动化访问。本工具使用住宅 IP 限速。如被拦截，等待后重试。

## 🛠️ 开发

```bash
uv sync --group dev
uv run ruff check src/
uv run pytest
```

## 📄 许可证

[MIT](LICENSE) © 2026 [Phat-Po](https://github.com/Phat-Po)

---

> 为需要理解中文互联网的 AI agent 而建。
> 如果 link-grabber 帮你省了时间，给个 ⭐ 吧。
