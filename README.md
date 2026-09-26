# JarMug

JarMug (Just a Rather Music Generator) is a local Windows desktop app for
generating music, solo instruments, and sound effects. Its CustomTkinter GUI
calls the same Stable Audio 3 backend as the CLI. Music and Instrument use
Small-Music; SFX uses Small-SFX. Prompts receive light mode-specific guidance.

The desktop app offers 10, 30, 60, and 120 second presets, background
generation with elapsed time, uniquely named WAV output, pygame-ce playback
with a position timeline, and a recent-generations browser. WAVs are written
to `D:\JarMug\output`. Model files use `G:\JarMug\Models\Stable-Audio`.

## Hardware Compatibility

JarMug has been developed and tested on Windows with an NVIDIA GeForce RTX 3060 (12 GB VRAM).

- Tested: RTX 3060 12 GB, CUDA 12.8, Windows.
- Other NVIDIA GPUs: May work with compatible CUDA support and sufficient VRAM, but have not been tested.
- AMD, Intel and CPU-only systems: Not currently tested or officially supported.
- Maximum tested duration: 120 seconds using Stable Audio 3 Small-Music.

## Requirements

- Windows with Python 3.11 or newer and a working audio output device.
- Sufficient free RAM and disk space for the Stable Audio 3 Small models,
  cached weights, and generated WAVs.
- A separately installed Stable Audio 3 runtime at
  `D:\JarMug\engines\stable_audio\.venv\Scripts\stable-audio.exe` and the
  Small-Music and Small-SFX model files in the configured cache.

The engine checkout, virtual environments, model weights, credentials, and
generated audio are local resources and are not stored in this repository.
Installing this repository alone does not install the engine or model weights.

## Models, access, and licenses

JarMug's original source code is licensed under the [MIT License](LICENSE).
This license does not cover third-party engines, model weights, or dependencies.
The Stable Audio 3 inference engine and model
weights are separate third-party components from Stability AI; neither is
included in this repository. JarMug invokes the locally installed engine and
uses the [Small-Music](https://huggingface.co/stabilityai/stable-audio-3-small-music)
and [Small-SFX](https://huggingface.co/stabilityai/stable-audio-3-small-sfx)
models. Their terms are governed by the
[Stability AI Community License](https://stability.ai/community-license-agreement)
and the conditions on each model page, including the
[Gemma Terms of Use](https://ai.google.dev/gemma/terms) for a Gemma component.

Each user must obtain their own access to both model repositories, accept the
applicable conditions, and authenticate locally with their own Hugging Face
account before generation. Keep credentials in a local credential store, never
in this repository. JarMug does not distribute model weights or access tokens.
The engine source is maintained separately at
[Stability-AI/stable-audio-3](https://github.com/Stability-AI/stable-audio-3)
under its [own MIT license](https://github.com/Stability-AI/stable-audio-3/blob/main/LICENSE).

**Powered by Stability AI.** See [NOTICE.txt](NOTICE.txt) for third-party model
attribution. A packaged application must also include the applicable license
and notices for any third-party code or models it distributes.

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
