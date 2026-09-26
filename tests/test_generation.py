import importlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from core import generation as gen
from core.prompts import enhance_prompt
from core.router import choose_model


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.engine = self.root / "stable-audio.exe"
        self.engine.touch()
        for name, value in (("STABLE_AUDIO_CLI", self.engine),
                            ("OUTPUT_DIR", self.root / "output"),
                            ("MODEL_CACHE", self.root / "cache")):
            patcher = patch.object(gen, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    @staticmethod
    def successful_run(command, **kwargs):
        Path(command[command.index("-o") + 1]).write_bytes(b"RIFF" + b"\0" * 100)
        return subprocess.CompletedProcess(command, 0)

    def test_routes_arguments_cache_and_status(self):
        for mode, model in (("music", "small-music"), ("instrument", "small-music"),
                            ("sfx", "small-sfx")):
            with self.subTest(mode=mode), patch.object(gen.subprocess, "run", side_effect=self.successful_run) as run:
                statuses = []
                with patch.dict(os.environ, {"HF_HOME": "parent-cache"}):
                    path = gen.generate_audio(mode, "warm piano", 30, on_status=statuses.append)
                    self.assertEqual(os.environ["HF_HOME"], "parent-cache")
                command = run.call_args.args[0]
                self.assertEqual(command, [str(self.engine), "--model", model, "-p",
                                          enhance_prompt(mode, "warm piano"), "--duration", "30", "-o", str(path)])
                self.assertEqual(run.call_args.kwargs["env"]["HF_HOME"], str(self.root / "cache"))
                self.assertNotIn("shell", run.call_args.kwargs)
                self.assertTrue(path.is_file())
                self.assertEqual(statuses[-1], "Generation complete.")

    def test_invalid_requests_do_not_start_engine(self):
        with patch.object(gen.subprocess, "run") as run:
            for mode, prompt, duration in (("bad", "piano", 10), ("music", "  ", 10),
                                           ("music", "piano", 0), ("sfx", "rain", 121),
                                           ("music", "piano", 1.5), ("music", "piano", True)):
                with self.subTest(mode=mode, duration=duration), self.assertRaises(ValueError):
                    gen.generate_audio(mode, prompt, duration)
            run.assert_not_called()

    def test_presets_and_unique_paths(self):
        for duration in (10, 30, 60, 120):
            self.assertEqual(gen.validate_duration(duration), duration)
        paths = {gen.create_output_path("music") for _ in range(100)}
        self.assertEqual(len(paths), 100)
        self.assertTrue(all(p.name.startswith("jarmug_music_") and p.suffix == ".wav" for p in paths))

    def test_missing_engine(self):
        self.engine.unlink()
        with self.assertRaisesRegex(FileNotFoundError, "engine not found"):
            gen.generate_audio("music", "piano")

    def test_engine_failure_includes_bounded_diagnostics_and_releases_lock(self):
        def fail(command, **kwargs):
            kwargs["stdout"].write(b"x" * 8000 + b"\nCUDA out of memory")
            return subprocess.CompletedProcess(command, 7)
        with patch.object(gen.subprocess, "run", side_effect=fail):
            with self.assertRaises(subprocess.CalledProcessError) as caught:
                gen.generate_audio("music", "piano")
        details = gen.describe_error(caught.exception)
        self.assertIn("exit code 7", details)
        self.assertIn("CUDA out of memory", details)
        self.assertLess(len(details), 6200)
        with patch.object(gen.subprocess, "run", side_effect=self.successful_run):
            self.assertTrue(gen.generate_audio("sfx", "rain").exists())

    def test_success_without_output_is_error(self):
        with patch.object(gen.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)):
            with self.assertRaisesRegex(RuntimeError, "without producing"):
                gen.generate_audio("music", "piano")

    def test_concurrent_backend_call_rejected(self):
        gen._generation_lock.acquire()
        try:
            with self.assertRaisesRegex(RuntimeError, "already running"):
                gen.generate_audio("music", "piano")
        finally:
            gen._generation_lock.release()

    def test_cli_import_has_no_prompt_or_directory_side_effect(self):
        with patch("builtins.input", side_effect=AssertionError("input called")), \
                patch.object(Path, "mkdir", side_effect=AssertionError("mkdir called")):
            import jarmug
            importlib.reload(jarmug)

    def test_cli_still_calls_shared_generator(self):
        import jarmug
        with patch("builtins.input", side_effect=["instrument", "soft flute", ""]), \
                patch("builtins.print"), patch.object(jarmug, "generate_audio", return_value=Path("clip.wav")) as generate:
            jarmug.main()
            self.assertEqual(generate.call_args.args, ("instrument", "soft flute", 10))

    def test_original_routing_and_prompt_rules(self):
        self.assertEqual(choose_model(" Instrument "), "small-music")
        self.assertEqual(choose_model("SFX"), "small-sfx")
        self.assertIn("Solo instrument only", enhance_prompt("instrument", "piano"))
        self.assertIn("Sound effect only", enhance_prompt("sfx", "rain"))


if __name__ == "__main__":
    unittest.main()
