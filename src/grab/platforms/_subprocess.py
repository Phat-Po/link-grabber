from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from ..utils import PROJECT_ROOT


def engine_python(engine_dir: Path) -> Path:
    candidates = [
        engine_dir / ".venv" / "bin" / "python",
        engine_dir / "venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path(sys.executable)


def run_worker(module: str, engine_dir: Path, payload: dict[str, object], timeout: int = 300) -> dict:
    python = engine_python(engine_dir)
    env = os.environ.copy()
    src = PROJECT_ROOT / "src"
    pieces = [str(src), str(engine_dir)]
    if env.get("PYTHONPATH"):
        pieces.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pieces)
    proc = subprocess.run(
        [
            str(python),
            "-m",
            module,
            json.dumps(payload, ensure_ascii=False),
        ],
        cwd=str(PROJECT_ROOT),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        env=env,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        raise RuntimeError(f"{module} failed ({proc.returncode}): {detail[-2000:]}")
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"{module} produced no output")
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{module} returned non-JSON output: {lines[-1][:500]}") from exc


def require_engine(name: str) -> Path:
    path = PROJECT_ROOT / "engines" / name
    if not path.exists():
        raise RuntimeError(
            f"Missing engine: {path}. Copy or clone it into engines/ before grabbing this platform."
        )
    return path
