# JarMug

JarMug (Just a Rather Music Generator) is a local Windows desktop app for
generating music, solo instruments, and sound effects. Its CustomTkinter GUI
calls the same Stable Audio 3 backend as the CLI. Music and Instrument use
Small-Music; SFX uses Small-SFX. Prompts receive light mode-specific guidance.

The desktop app offers 10, 30, 60, and 120 second presets, background
generation with elapsed time, uniquely named WAV output, pygame-ce playback
with a position timeline, and a recent-generations browser. WAVs are written
to `D:\JarMug\output`. Model files use `G:\JarMug\Models\Stable-Audio`.

## Requirements

- Windows with Python 3.11 or newer and a working audio output device.
- Sufficient free RAM and disk space for the Stable Audio 3 Small models,
  cached weights, and generated WAVs. The Small models support CPU inference;
  generation can be slow without a suitable accelerator. A GPU is optional.
- A separately installed Stable Audio 3 runtime at
  `D:\JarMug\engines\stable_audio\.venv\Scripts\stable-audio.exe` and the
  Small-Music and Small-SFX model files in the configured cache.

The engine checkout, virtual environments, model weights, credentials, and
generated audio are local resources and are not stored in this repository.
Installing this repository alone does not install the engine or model weights.

## Setup and launch

For the existing local setup, open PowerShell in `D:\JarMug`:

```powershell
.\.venv-gui\Scripts\python.exe gui.py
```

To recreate only the lightweight GUI environment with an existing Python
3.11+ installation:

```powershell
python -m venv .venv-gui
.\.venv-gui\Scripts\python.exe -m pip install -r requirements-gui.txt
```

Keep `.venv-gui` separate from the Stable Audio engine environment. The GUI
environment needs CustomTkinter and pygame-ce, not a second PyTorch install.
For more Windows setup and usage details, see [GUI_SETUP.md](GUI_SETUP.md).

The CLI remains available:

```powershell
.\.venv\Scripts\python.exe jarmug.py
```

Run the non-generation checks without loading models:

```powershell
.\.venv-gui\Scripts\python.exe -m unittest discover -s tests -v
```

The playback timeline displays position and duration. Seeking is not offered
for WAV files because the current pygame-ce playback path does not support it
reliably.
