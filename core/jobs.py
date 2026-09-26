"""Thread/queue bridge with no dependency on Tk or an audio library."""

from queue import Empty, Queue
from threading import Thread

from core.generation import describe_error, generate_audio


class GenerationJob:
    """start() and poll() belong to the UI thread; workers only write the queue."""

    def __init__(self, generator=generate_audio):
        self.generator = generator
        self.busy = False
        self.events = Queue()

    def start(self, mode, prompt, duration):
        if self.busy:
            return False
        self.busy = True
        try:
            Thread(target=self._run, args=(mode, prompt, duration), daemon=False).start()
        except Exception:
            self.busy = False
            raise
        return True

    def _run(self, mode, prompt, duration):
        try:
            path = self.generator(mode, prompt, duration,
                                  on_status=lambda text: self.events.put(("status", text)))
            self.events.put(("done", path))
        except Exception as error:
            self.events.put(("error", describe_error(error)))

    def poll(self):
        events = []
        while True:
            try:
                event = self.events.get_nowait()
            except Empty:
                break
            if event[0] in ("done", "error"):
                self.busy = False
            events.append(event)
        return events
