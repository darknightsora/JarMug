from pathlib import Path
from threading import Event, get_ident
import time
import unittest
from unittest.mock import patch

from core.jobs import GenerationJob


class JobTests(unittest.TestCase):
    def wait_events(self, job):
        events = []
        deadline = time.monotonic() + 3
        while job.busy and time.monotonic() < deadline:
            events.extend(job.poll())
            time.sleep(0.005)
        self.assertFalse(job.busy)
        return events

    def test_thread_queue_and_duplicate_clicks(self):
        release = Event()
        entered = Event()
        worker_threads = []
        def fake(*args, on_status):
            worker_threads.append(get_ident())
            entered.set()
            on_status("working")
            release.wait(3)
            return Path("result.wav")
        job = GenerationJob(fake)
        try:
            self.assertTrue(job.start("music", "piano", 10))
            self.assertTrue(entered.wait(2))
            self.assertFalse(job.start("music", "piano", 10))
            self.assertTrue(job.busy)
        finally:
            release.set()
        events = self.wait_events(job)
        self.assertEqual(events, [("status", "working"), ("done", Path("result.wav"))])
        self.assertNotEqual(worker_threads[0], get_ident())

    def test_failure_can_be_retried(self):
        def fail(*args, **kwargs):
            raise RuntimeError("engine failed")
        job = GenerationJob(fail)
        job.start("sfx", "rain", 10)
        self.assertEqual(self.wait_events(job), [("error", "engine failed")])
        job.generator = lambda *args, **kwargs: Path("retry.wav")
        self.assertTrue(job.start("sfx", "rain", 10))
        self.assertEqual(self.wait_events(job), [("done", Path("retry.wav"))])

    def test_thread_start_failure_resets_busy(self):
        job = GenerationJob()
        with patch("core.jobs.Thread.start", side_effect=RuntimeError("no threads")):
            with self.assertRaises(RuntimeError):
                job.start("music", "piano", 10)
        self.assertFalse(job.busy)
