# JarMug GUI — Windows setup

JarMug's desktop GUI is `D:\JarMug\gui.py`. It shares the existing
`core\generation.py` backend and uses the Stable Audio 3 executable in
`engines\stable_audio\.venv`. Music and Instrument use small-music; SFX uses
small-sfx. Generated WAVs are saved in `D:\JarMug\output` and the engine's
Hugging Face cache remains `G:\JarMug\Models\Stable-Audio`.

## Launch

From PowerShell:

```powershell
cd D:\JarMug
.\.venv-gui\Scripts\python.exe gui.py
```

The GUI has its own `.venv-gui` environment with CustomTkinter and pygame-ce.
It does not need PyTorch in that environment. Keep it separate from the
existing Stable Audio environment; do not replace either environment or the
working CLI and `core` files.

If `.venv-gui` needs to be recreated on a new machine, use Python 3.11+ and
install the lightweight requirements from `requirements-gui.txt`:

```powershell
python -m venv .venv-gui
.\.venv-gui\Scripts\python.exe -m pip install -r requirements-gui.txt
```

## Using the GUI

Select Music, Instrument, or SFX, enter a prompt, choose 10, 30, 60, or 120
seconds, and click Generate audio. The window remains responsive while the
engine runs and shows elapsed generation time and the engine's status message.
Afterward it shows the WAV filename and duration. Play and Stop control the
selected WAV through pygame-ce. The timeline displays elapsed and total
playback time; it does not offer seeking because pygame-ce does not reliably
seek within WAV files. Recent generations lists up to six WAVs already in the
output folder; click one to select it, or use Refresh after adding files by
other means. Open Output Folder opens `D:\JarMug\output` in Explorer.

Only one generation runs at a time. If generation is active, wait for it to
finish before closing the window; closing does not cancel the engine process.
The CLI remains available as `.\.venv\Scripts\python.exe jarmug.py`.

Run the non-generation checks with:

```powershell
.\.venv-gui\Scripts\python.exe -m unittest discover -s tests -v
```
