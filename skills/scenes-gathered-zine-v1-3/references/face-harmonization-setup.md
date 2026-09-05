# Optional face harmonization setup

The default Gathered Scenes workflow has no local runtime dependency. Prepare this environment only when the user explicitly requests source-face preservation or face repair.

Requirements:

- Node.js 22 or newer
- Python 3.12

Windows PowerShell:

```powershell
Set-Location "$env:USERPROFILE\.codex\skills\scenes-gathered-zine-v1-3"
npm ci
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-face.txt
npm test
```

macOS or Linux:

```bash
cd ~/.codex/skills/scenes-gathered-zine-v1-3
npm ci
python3.12 -m venv .venv
./.venv/bin/python -m pip install -r requirements-face.txt
npm test
```

The bundled model source and checksum are recorded in `assets/face-harmonization-model.json`. Do not commit `.venv`, `node_modules`, user photos, generated images, or task intermediates.
