"""Lazy, local WAV playback. No audio device is opened until Play is pressed."""

import os
import struct


def wav_duration(path):
    """Return WAV length from RIFF chunks, including IEEE float WAVs.

    Read only headers; large generated audio is never loaded into memory.
    Invalid or partial files have no duration.
    """
    try:
        file_size = path.stat().st_size
        with path.open("rb") as source:
            header = source.read(12)
            if len(header) != 12 or header[:4] != b"RIFF" or header[8:] != b"WAVE":
                return None
            fmt = None
            data_size = None
            while source.tell() + 8 <= file_size:
                chunk = source.read(8)
                chunk_type, chunk_size = struct.unpack("<4sI", chunk)
                chunk_end = source.tell() + chunk_size
                if chunk_end > file_size:
                    return None
                if chunk_type == b"fmt ":
                    if chunk_size < 16:
                        return None
                    fmt = struct.unpack("<HHIIHH", source.read(16))
                elif chunk_type == b"data":
                    data_size = chunk_size
                if fmt is not None and data_size is not None:
                    format_tag, channels, sample_rate, byte_rate, block_align, _ = fmt
                    if (format_tag not in (1, 3, 65534) or channels < 1 or
                            sample_rate < 1 or byte_rate < 1 or block_align < 1 or
                            byte_rate != sample_rate * block_align or
                            data_size % block_align):
                        return None
                    return data_size / byte_rate
                source.seek(chunk_end + (chunk_size & 1))
    except (OSError, ValueError, struct.error):
        return None
    return None


class WavPlayer:
    def __init__(self):
        self._mixer = None

    def play(self, path):
        if not path.is_file():
            raise FileNotFoundError(f"Audio file no longer exists:\n{path}")
        if self._mixer is None:
            os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
            from pygame import mixer
            self._mixer = mixer
        if not self._mixer.get_init():
            self._mixer.init()
        self._mixer.music.load(str(path))
        self._mixer.music.play()

    def stop(self):
        if self._mixer is not None and self._mixer.get_init():
            self._mixer.music.stop()
            self._mixer.music.unload()

    def is_playing(self):
        return bool(self._mixer is not None and self._mixer.get_init()
                    and self._mixer.music.get_busy())

    def position(self):
        if not self.is_playing():
            return 0.0
        return max(0.0, self._mixer.music.get_pos() / 1000.0)

    def close(self):
        if self._mixer is not None:
            self._mixer.quit()
