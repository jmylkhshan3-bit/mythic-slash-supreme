from __future__ import annotations

import shutil


def resolve_ffmpeg_executable() -> str:
    path = shutil.which('ffmpeg')
    if path:
        return path
    try:
        import imageio_ffmpeg  # type: ignore

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # pragma: no cover - fallback path
        raise RuntimeError('ffmpeg was not found. Install ffmpeg or add imageio-ffmpeg.') from exc
