import tempfile
import time
import unittest
import wave
from pathlib import Path

from core import library


def make_wav(path, seconds):
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(b"\0\0" * (8000 * seconds))


class LibraryTests(unittest.TestCase):
    def test_recent_wavs_are_newest_first_and_limited(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            for index in range(8):
                path = folder / f"track_{index}.wav"
                make_wav(path, index + 1)
                stamp = time.time() + index * 2
                import os
                os.utime(path, (stamp, stamp))
            (folder / "notes.txt").write_text("ignore")
            items = library.recent_wavs(folder, limit=5)
            self.assertEqual([item.path.name for item in items],
                             ["track_7.wav", "track_6.wav", "track_5.wav",
                              "track_4.wav", "track_3.wav"])
            self.assertEqual(items[0].duration, 8.0)

    def test_missing_folder_and_invalid_wav_are_safe(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            self.assertEqual(library.recent_wavs(folder / "missing"), [])
            (folder / "broken.wav").write_bytes(b"bad")
            items = library.recent_wavs(folder)
            self.assertEqual(len(items), 1)
            self.assertIsNone(items[0].duration)
