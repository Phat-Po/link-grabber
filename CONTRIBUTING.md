# Contributing to link-grabber

Thanks for your interest in contributing! This document outlines how to get started.

## Development Setup

```bash
git clone https://github.com/Phat-Po/link-grabber.git
cd link-grabber
uv sync --group dev
uv run playwright install chromium
```

## Running Tests

```bash
uv run pytest
```

## Code Style

We use [Ruff](https://github.com/astral-sh/ruff) for linting:

```bash
uv run ruff check src/
uv run ruff format src/
```

## Project Structure

```
src/grab/
├── cli.py              # Typer CLI entry point
├── detect.py           # URL → platform detection
├── models.py           # Data models (Pydantic)
├── pack.py             # Context pack generation (manifest.md)
├── comprehend.py       # Video comprehension (ffmpeg + Whisper)
├── archive.py          # Obsidian archive layer
├── utils.py            # Shared utilities
└── platforms/
    ├── xhs.py          # Xiaohongshu adapter
    ├── douyin.py        # Douyin adapter
    └── weixin.py        # WeChat adapter
```

## Adding a New Platform

1. Create `src/grab/platforms/<platform>.py`
2. Implement `async def grab_<platform>(url: str, out_root: Path) -> GrabResult`
3. Add URL pattern to `detect.py`
4. Register in `cli.py`
5. Add tests

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Make your changes
4. Run `uv run ruff check src/` and `uv run pytest`
5. Commit with a clear message
6. Open a Pull Request

## Reporting Issues

Open an issue on [GitHub Issues](https://github.com/Phat-Po/link-grabber/issues) with:
- What you were trying to do
- What happened instead
- Steps to reproduce
- Your Python version and OS

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
