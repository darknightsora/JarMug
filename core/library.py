"""Read-only browser for WAV files already in JarMug's output folder."""

from dataclasses import dataclass
from pathlib import Path

from core.playback import wav_duration


@dataclass(frozen=True)
class RecentWav:
    path: Path
    duration: float | None


def recent_wavs(folder: Path, limit: int = 6) -> list[RecentWav]:
    try:
        paths = (path for path in folder.iterdir()
                 if path.is_file() and path.suffix.lower() == ".wav")
        newest = sorted(paths, key=lambda path: path.stat().st_mtime, reverse=True)
        return [RecentWav(path, wav_duration(path)) for path in newest[:limit]]
    except (FileNotFoundError, PermissionError, OSError):
        return []
