import os
from pathlib import Path
import tempfile
from threading import Event, get_ident
import time
import unittest
from unittest.mock import Mock, patch
import wave

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import customtkinter as ctk
from gui import JarMugApp
from core.jobs import GenerationJob
from core.playback import WavPlayer


class GuiTests(unittest.TestCase):
    def setUp(self):
        ctk.set_appearance_mode("dark")
        self.player = Mock()
        self.player.is_playing.return_value = True
        self.job = GenerationJob(lambda *args, **kwargs: Path("test.wav"))
        self.app = JarMugApp(self.job, self.player)
        self.app.withdraw()
        self.errors = patch("gui.messagebox.showerror")
        self.error_box = self.errors.start()
        self.addCleanup(self.errors.stop)
        self.addCleanup(self.close_app)

    def close_app(self):
        # Multiple Tk roots in this test process otherwise retain CustomTkinter
        # timers from destroyed interpreters. Cancel all timers before teardown.
        for timer in self.app.tk.call("after", "info"):
            self.app.tk.call("after", "cancel", timer)
        self.app.destroy()

    def pump_until_done(self):
        deadline = time.monotonic() + 3
        while self.job.busy and time.monotonic() < deadline:
            self.app.update()
            time.sleep(0.01)
        self.assertFalse(self.job.busy)
        self.app.update()

    def test_empty_prompt_and_initial_playback(self):
        self.app._generate()
        self.assertFalse(self.job.busy)
        self.assertEqual(self.app.play_button.cget("state"), "disabled")
        self.assertIn("Describe", self.app.status.cget("text"))

    def test_success_responsive_controls_and_ui_thread(self):
        release = Event()
        calls = []
        ui_threads = []
        original_configure = self.app.status.configure
        def tracked_configure(*args, **kwargs):
            ui_threads.append(get_ident())
            return original_configure(*args, **kwargs)
        def fake(*args, on_status):
            calls.append(args)
            on_status("Fake engine working")
            release.wait(3)
            return Path("test.wav")
        self.job.generator = fake
        self.app.status.configure = tracked_configure
        self.app.prompt.insert("1.0", "soft piano")
        self.app.mode.set("Instrument")
        self.app.duration.set("120s")
        try:
            self.app._generate()
            self.app._generate()
            self.assertEqual(self.app.generate_button.cget("state"), "disabled")
            heartbeat = []
            self.app.after(1, lambda: heartbeat.append(True))
            deadline = time.monotonic() + 0.3
            while time.monotonic() < deadline:
                self.app.update()
                time.sleep(0.01)
            self.assertTrue(heartbeat)
            with patch("gui.messagebox.showinfo") as notice:
                self.app._close()
                notice.assert_called_once()
            self.assertTrue(self.app.winfo_exists())
        finally:
            release.set()
        self.pump_until_done()
        self.assertEqual(calls, [("instrument", "soft piano", 120)])
        self.assertEqual(self.app.generate_button.cget("state"), "normal")
        self.assertEqual(self.app.play_button.cget("state"), "normal")
        self.assertEqual(self.app.output_path, Path("test.wav"))
        self.assertEqual(set(ui_threads), {get_ident()})

    def test_error_restores_controls_and_keeps_previous_output(self):
        def fail(*args, **kwargs):
            raise RuntimeError("Test engine failure")
        self.job.generator = fail
        self.app.output_path = Path("previous.wav")
        self.app.prompt.insert("1.0", "rain")
        self.app._generate()
        self.pump_until_done()
        self.assertEqual(self.app.generate_button.cget("state"), "normal")
        self.assertEqual(self.app.output_path, Path("previous.wav"))
        self.error_box.assert_called_once()

    def test_play_stop_completion_and_audio_error(self):
        self.app.output_path = Path("test.wav")
        self.app._play()
        self.player.play.assert_called_once_with(Path("test.wav"))
        self.assertTrue(self.app.playing)
        self.app._stop()
        self.assertFalse(self.app.playing)
        self.app._play()
        self.player.is_playing.return_value = False
        self.app.after_cancel(self.app._poll_id)
        self.app._poll()
        self.assertFalse(self.app.playing)
        self.player.play.side_effect = RuntimeError("No audio device")
        self.app._play()
        self.assertFalse(self.app.playing)
        self.error_box.assert_called_once()

    def test_output_folder_and_failure(self):
        with tempfile.TemporaryDirectory() as temp, patch("gui.OUTPUT_DIR", Path(temp)), \
                patch("gui.os.startfile", create=True) as startfile:
            self.app._open_output()
            startfile.assert_called_once_with(temp)
            startfile.side_effect = OSError("Explorer unavailable")
            self.app._open_output()
            self.error_box.assert_called_once()

    def test_track_timeline_uses_wav_length_and_playback_clock(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "recent.wav"
            with wave.open(str(path), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(8000)
                wav.writeframes(b"\0\0" * 16000)
            self.app._select_output(path)
            self.assertEqual(self.app.timeline_label.cget("text"), "0:00 / 0:02")
            self.app._play()
            self.player.position.return_value = 0.75
            self.app.after_cancel(self.app._poll_id)
            self.app._poll()
            self.assertEqual(self.app.timeline_label.cget("text"), "0:00 / 0:02")
            self.assertAlmostEqual(self.app.timeline.get(), 0.375, places=2)
            self.player.position.return_value = 1.2
            self.app.after_cancel(self.app._poll_id)
            self.app._poll()
            self.assertEqual(self.app.timeline_label.cget("text"), "0:01 / 0:02")
            self.app._stop()
            self.assertEqual(self.app.timeline_label.cget("text"), "0:00 / 0:02")

    def test_generation_status_shows_elapsed_and_success(self):
        release = Event()
        def fake(*args, on_status):
            on_status("Generating 10s with small-music.")
            release.wait(3)
            return Path("finished.wav")
        self.job.generator = fake
        self.app.prompt.insert("1.0", "piano")
        try:
            self.app._generate()
            self.app.started_at = time.monotonic() - 65
            self.app.after_cancel(self.app._poll_id)
            self.app._poll()
            self.assertIn("1:05", self.app.status.cget("text"))
            self.assertIn("Generating", self.app.status.cget("text"))
        finally:
            release.set()
        self.pump_until_done()
        self.assertIn("complete", self.app.status.cget("text").lower())
        self.assertIn("1:05", self.app.status.cget("text"))

    def test_generation_failure_status_names_error_and_elapsed(self):
        def fail(*args, **kwargs):
            raise RuntimeError("engine unavailable")
        self.job.generator = fail
        self.app.prompt.insert("1.0", "rain")
        self.app._generate()
        self.app.started_at = time.monotonic() - 12
        self.pump_until_done()
        status = self.app.status.cget("text")
        self.assertIn("failed", status.lower())
        self.assertIn("0:12", status)

    def test_recent_generations_can_be_selected_and_show_duration(self):
        with tempfile.TemporaryDirectory() as temp, patch("gui.OUTPUT_DIR", Path(temp)):
            newest = Path(temp) / "newest.wav"
            older = Path(temp) / "older.wav"
            for path, seconds in ((newest, 2), (older, 1)):
                with wave.open(str(path), "wb") as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(8000)
                    wav.writeframes(b"\0\0" * (8000 * seconds))
            import os as system_os
            now = time.time()
            system_os.utime(older, (now - 10, now - 10))
            system_os.utime(newest, (now, now))
            self.app._refresh_recent()
            self.assertEqual(len(self.app.recent_buttons), 2)
            self.assertIn("newest.wav", self.app.recent_buttons[0].cget("text"))
            self.app.recent_buttons[1].invoke()
            self.assertEqual(self.app.output_path, older)
            self.assertIn("older.wav", self.app.file_label.cget("text"))
            self.assertIn("0:01", self.app.file_label.cget("text"))
            self.assertEqual(self.app.timeline_label.cget("text"), "0:00 / 0:01")

    def test_controls_fit_at_minimum_window_size(self):
        self.app.deiconify()
        self.app.geometry("600x700")
        self.app.update()
        time.sleep(0.1)
        self.app.update()
        self.assertTrue(self.app.prompt.winfo_ismapped())
        self.assertGreaterEqual(self.app.prompt.winfo_height(), 130)
        canvas = self.app.content._parent_canvas
        self.assertLess(canvas.yview()[1], 1.0)
        canvas.yview_moveto(1.0)
        self.app.update()
        self.assertTrue(self.app.recent_list.winfo_ismapped())
        self.assertLessEqual(self.app.recent_list.winfo_rooty() + self.app.recent_list.winfo_height(),
                             self.app.winfo_rooty() + self.app.winfo_height())
        self.app.withdraw()


class PlaybackTests(unittest.TestCase):
    def test_real_wav_with_dummy_device(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {"SDL_AUDIODRIVER": "dummy"}):
            path = Path(temp) / "test.wav"
            with wave.open(str(path), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(44100)
                wav.writeframes(b"\0\0" * 44100)
            player = WavPlayer()
            try:
                player.play(path)
                self.assertTrue(player.is_playing())
                player.stop()
                self.assertFalse(player.is_playing())
                path.unlink()  # Stop must release the file handle on Windows.
                with self.assertRaises(FileNotFoundError):
                    player.play(path)
            finally:
                player.close()

    def test_invalid_wav_can_be_closed(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {"SDL_AUDIODRIVER": "dummy"}):
            path = Path(temp) / "bad.wav"
            path.write_bytes(b"not a wave file")
            player = WavPlayer()
            try:
                with self.assertRaises(Exception):
                    player.play(path)
            finally:
                player.close()
