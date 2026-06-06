# link-grabber

把内容链接（小红书 / 抖音 / 微信公众号，图文或视频）变成 **AI agent 能直接读懂的形态**，让任意 project、任意 agent 拿到链接就能理解内容并完成任务。

## 它解决什么
你在任何地方对 agent 说「参考这几个链接帮我写 X」并贴上 1–5 条链接，agent 自动：抓取内容 → 看懂（读文字 / 看图上的字 / 看视频画面 + 听语音转录）→ 基于理解产出你要的东西。

## 形态
- **CLI**：`grab <url>` → 产出 context-pack（`manifest.md` + 图 / 视频帧 / 转录）
- **全局 Skill**：`~/.claude/skills/link-grabber/`，任意 Claude agent 可调
- **可选存档**：`grab <url> --save-obsidian` → AI 分类摘要写进 Obsidian `WeChat/{分类}/`

## 平台支持
| 平台 | 内容 | 理解方式 |
|------|------|---------|
| 小红书 | 图文 / 视频 | 看图+读标题文案；视频抽帧+转录 |
| 抖音 | 视频 | 关键帧 + Whisper 转录 |
| 微信公众号 | 图文（新旧两版） | 读正文 + 看图 |

## 安装
```bash
uv sync
uv run playwright install chromium
uv run grab --help
```

视频转录使用 OpenAI Whisper API，读取环境变量 `OPENAI_API_KEY`。默认会转录视频；如只需要画面关键帧：

```bash
uv run grab "<url>" --no-transcript
```

## 使用
```bash
uv run grab "http://xhslink.com/o/3GATQJP3HgA"
uv run grab "https://v.douyin.com/16opyW1Vvmo/" --no-transcript
uv run grab "https://mp.weixin.qq.com/s/Oo0iksfTXvUSFNnBrWOOpw" --json
```

默认输出到 `~/.cache/link-grabber/<platform>_<id>/`，并打印 `manifest.md` 绝对路径。agent 应读取 `manifest.md`，再查看其中列出的图片和视频帧。

## 归档到 Obsidian
仅在显式加 `--save-obsidian` 时写入 Obsidian：

```bash
uv run grab "<url>" --save-obsidian
```

需要环境变量：
- `OPENAI_API_KEY`
- `OBSIDIAN_API_KEY`
- `OBSIDIAN_PORT`，默认 `27123`

写入路径为 `WeChat/{AI分类}/YYYY-MM-DD_title.md`，格式与 `wechat-article-summary` 扩展保持一致。

## 安全边界
- 不登录，不发送平台 Cookie。
- 公众号使用无登录 Playwright 渲染；遇到「环境异常」会停止并报错。
- 写 Obsidian 是 opt-in，默认只生成本地 context-pack。
- Whisper 约按分钟计费；用 `--no-transcript` 可跳过。

## 状态
🟢 MVP 已实现。执行规格：[`tasks/TASK-001-build-link-grabber.md`](tasks/TASK-001-build-link-grabber.md)
