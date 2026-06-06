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

## 状态
🟡 规划完成，待实现。执行规格：[`tasks/TASK-001-build-link-grabber.md`](tasks/TASK-001-build-link-grabber.md)

## Setup（实现后）
```bash
uv sync
cp .env.example .env   # 填 OBSIDIAN_API_KEY（OPENAI_API_KEY 走环境变量）
uv run grab "<url>"
```
