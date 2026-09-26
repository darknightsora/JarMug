"""Shared Stable Audio subprocess adapter; importing this module has no side effects."""

import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Callable
from uuid import uuid4

from core.prompts import enhance_prompt
from core.router import VALID_OUTPUT_TYPES, choose_model

JARMUG_ROOT = Path(r"D:\JarMug")
OUTPUT_DIR = JARMUG_ROOT / "output"
STABLE_AUDIO_CLI = JARMUG_ROOT / "engines/stable_audio/.venv/Scripts/stable-audio.exe"
MODEL_CACHE = Path(r"G:\JarMug\Models\Stable-Audio")
MIN_DURATION = 1
MAX_DURATION = 120
_generation_lock = Lock()


def create_output_path(output_type: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return OUTPUT_DIR / f"jarmug_{output_type}_{timestamp}_{uuid4().hex[:8]}.wav"


def validate_duration(duration: int) -> int:
    if isinstance(duration, bool) or not isinstance(duration, int):
        raise ValueError("Duration must be a whole number of seconds.")
    if not MIN_DURATION <= duration <= MAX_DURATION:
        raise ValueError(f"Duration must be between {MIN_DURATION} and {MAX_DURATION} seconds.")
    return duration


def generate_audio(output_type: str, prompt: str, duration: int = 10,
                   *, on_status: Callable[[str], None] | None = None) -> Path:
    """Generate synchronously. Status callbacks run on the calling thread.

    Call from a worker in graphical clients. Engine output is spooled to disk
    rather than an unbounded pipe; only a bounded tail is included on failure.
    """
    output_type = output_type.strip().lower()
    if output_type not in VALID_OUTPUT_TYPES:
        raise ValueError(f"Output type must be: {', '.join(VALID_OUTPUT_TYPES)}")
    validate_duration(duration)
    final_prompt = enhance_prompt(output_type, prompt)
    model = choose_model(output_type)
    if not _generation_lock.acquire(blocking=False):
        raise RuntimeError("A generation is already running. Please wait for it to finish.")
    try:
        if not STABLE_AUDIO_CLI.is_file():
            raise FileNotFoundError(f"Stable Audio engine not found:\n{STABLE_AUDIO_CLI}")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        MODEL_CACHE.mkdir(parents=True, exist_ok=True)
        output_path = create_output_path(output_type)
        environment = os.environ.copy()
        environment["HF_HOME"] = str(MODEL_CACHE)
        command = [str(STABLE_AUDIO_CLI), "--model", model, "-p", final_prompt,
                   "--duration", str(duration), "-o", str(output_path)]
        if on_status:
            on_status(f"Generating {duration}s with {model}. Model loading may take a while.")
        with tempfile.TemporaryFile() as log:
            result = subprocess.run(
                command, env=environment, stdout=log, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                check=False,
            )
            if result.returncode:
                log.seek(0, os.SEEK_END)
                log.seek(max(0, log.tell() - 6000))
                details = log.read().decode("utf-8", errors="replace").strip()
                raise subprocess.CalledProcessError(result.returncode, command, output=details)
        if not output_path.is_file() or output_path.stat().st_size <= 44:
            raise RuntimeError("Stable Audio finished without producing a usable WAV file.")
        if on_status:
            on_status("Generation complete.")
        return output_path
    finally:
        _generation_lock.release()


def describe_error(error: Exception) -> str:
    if isinstance(error, subprocess.CalledProcessError):
        details = str(error.output or "No engine diagnostics were returned.")
        return f"Stable Audio failed (exit code {error.returncode}).\n\n{details}"
    if isinstance(error, PermissionError):
        return f"Access denied. Check access to the engine, output folder, and G: model cache.\n\n{error}"
    return str(error) or type(error).__name__
