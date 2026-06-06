# link-grabber — Status

## ▲ Current

## 2026-06-05 | 项目立项 + 完整执行规格就绪（待实现）

**Done this session:**
- 在 _playground 完成三平台调研 + 实测（小红书 XHS-Downloader、抖音 Douyin_TikTok_Download_API、微信公众号 Playwright 抽取）
- 公众号→Obsidian 全链路 PoC 已跑通（AI 分类摘要 + 写真实库），代码在 `_playground/scratch/20260605-wechat-batch-obsidian/`
- 架构定案：抽取内核 + 两消费者（用法B 喂 agent / 用法A 存 Obsidian）
- 三项关键决策确认：全局 Skill+CLI / 视频关键帧+Whisper转录 / 新建正式 project
- 写出完整执行规格 `tasks/TASK-001-build-link-grabber.md`
- 建好项目骨架（治理文档），未写实现代码

**Current state:**
- 骨架就绪，src/ 与 engines/ 未建。下一个 agent 按 TASK-001 执行即可。
- 三个引擎已在 _playground/scratch 验证可用，迁入 engines/ 即可复用。

**Next steps:**
1. 下一个 agent 读 `tasks/TASK-001-build-link-grabber.md`，按 Phase 1→5 执行
2. 用 task doc 内附的样本链接做全平台验收

**Decisions / notes:**
- 微信归档目录 = `WeChat/{中文分类}/`（沿用扩展，AI 自动分类）
- 小红书新增要求：每篇独立 folder + 标题/文案存 markdown（原本只下媒体）
- 视频转录用 OpenAI Whisper API（本机无 whisper，ffmpeg 8.0 已就位）
- 安全：无登录、公众号住宅IP限速、Obsidian 仅 --save-obsidian 时写

## ■ Milestones

## ▼ Archive
