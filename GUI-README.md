# JarMug v0.1 desktop

From PowerShell in `D:\JarMug`:

```powershell
.\.venv-gui\Scripts\python.exe gui.py
```

If setting up on another machine, create a separate Python 3.11+ environment
and install only the GUI requirements:

```powershell
python -m venv .venv-gui
.\.venv-gui\Scripts\python.exe -m pip install -r requirements-gui.txt
```

Choose Music, Instrument, or SFX, enter a description, choose a duration, and
press Generate. The status line shows elapsed generation time. The selected
track shows its filename, duration, and a playback timeline. Play restarts it;
Stop releases it. The recent browser lists up to six WAVs from the output
folder; click one to select it. Seeking is unavailable for these WAVs in
pygame-ce. Open Output Folder opens `D:\JarMug\output`. Errors retain the last
successful selection. Generation runs in a worker; the window stays responsive.
Close is deferred until generation finishes so the engine is not left running
unattended. The content area scrolls on smaller screens.

The CLI still runs with `.\.venv\Scripts\python.exe jarmug.py`.
Both entry points use `core/generation.py` and the existing engine executable
`engines\stable_audio\.venv\Scripts\stable-audio.exe`. Music/Instrument use
small-music; SFX uses small-sfx. The subprocess alone receives
`HF_HOME=G:\JarMug\Models\Stable-Audio`. Neither GUI dependency installs PyTorch.
Existing engine/cache setup is required; first engine use may download models
if they are not already cached. The GUI adds no online service.

Non-generation checks (mocked engine, temporary WAVs, dummy audio device):

```powershell
.\.venv-gui\Scripts\python.exe -m unittest discover -s tests -v
```
