from __future__ import annotations

import shutil
from pathlib import Path


def cleanup_generated_cache(
    generated_root: Path,
    keep_latest: int = 2,
) -> None:
    if keep_latest < 1:
        keep_latest = 1

    if not generated_root.exists():
        return

    render_dirs = [
        path
        for path in generated_root.iterdir()
        if path.is_dir()
    ]

    render_dirs.sort(
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    dirs_to_delete = render_dirs[keep_latest:]

    for render_dir in dirs_to_delete:
        shutil.rmtree(render_dir, ignore_errors=True)