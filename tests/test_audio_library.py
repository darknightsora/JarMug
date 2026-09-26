import struct
import tempfile
import unittest
from pathlib import Path

from core import playback
from core.playback import WavPlayer


class WavInfoTests(unittest.TestCase):
    def test_float_wav_duration_with_extra_chunk(self):
        # Stable Audio emits IEEE float WAVs. Python 3.11's wave rejects fmt tag 3.
        fmt = struct.pack("<HHIIHH", 3, 2, 44100, 352800, 8, 32)
        chunks = b"LIST" + struct.pack("<I", 4) + b"INFO"
        chunks += b"fmt " + struct.pack("<I", len(fmt)) + fmt
        chunks += b"data" + struct.pack("<I", 3528000) + b"\0" * 3528000
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "float.wav"
            path.write_bytes(b"RIFF" + struct.pack("<I", len(chunks) + 4) + b"WAVE" + chunks)
            self.assertEqual(playback.wav_duration(path), 10.0)

    def test_bad_or_truncated_wav_has_no_duration(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.wav"
            path.write_bytes(b"not a wav")
            self.assertIsNone(playback.wav_duration(path))
            path.write_bytes(b"RIFF\0\0\0\0WAVEfmt ")
            self.assertIsNone(playback.wav_duration(path))


class PlaybackPositionTests(unittest.TestCase):
    def test_position_uses_mixer_clock_and_resets_on_stop(self):
        class Music:
            playing = True

            def get_pos(self):
                return 2350

            def get_busy(self):
                return self.playing

            def stop(self):
                self.playing = False

            def unload(self):
                pass

        class Mixer:
            music = Music()

            def get_init(self):
                return True

        player = WavPlayer()
        player._mixer = Mixer()
        self.assertAlmostEqual(player.position(), 2.35)
        player.stop()
        self.assertEqual(player.position(), 0.0)
