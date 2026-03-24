# ComfyUI Storage Migrator Pro

A simple GUI tool to safely migrate your **ComfyUI** installation from one storage location to another — with real-time progress tracking, config auto-update, pause/resume, cancel, and undo support.

## Features

- 📁 **Browse & Select** source and destination folders via GUI
- 📊 **Live progress bar** showing copy progress by bytes
- ⏸️ **Pause / Resume** migration at any time
- ❌ **Cancel** mid-migration with automatic cleanup of partial files
- 🔄 **Undo** last migration (reverts configs and deletes the copied folder)
- 🗑️ Optional **delete original folder** after successful migration
- ⚙️ **Auto-updates ComfyUI config files**:
  - `%APPDATA%\ComfyUI\extra_models_config.yaml` — updates `base_path`
  - `%APPDATA%\ComfyUI\config.json` — updates `installPath`

## Requirements

- Python 3.x
- No external dependencies — uses only Python standard library (`tkinter`, `shutil`, `os`, `json`, `threading`)

## Usage

```bash
python COMFY_MIGRATOR.py
```

1. Select your **current ComfyUI folder** (source)
2. Select your **new destination folder**
3. (Optional) Check the box to delete the original folder after migration
4. Click **Start Migration**

## Notes

- If the destination folder is non-empty, the source folder will be copied **into** a subdirectory inside it.
- Config files are searched for in `%APPDATA%\ComfyUI\`. If none are found, a warning is shown (common with portable installs).
- The **Undo** button is only available if the original source folder was not deleted.

## Support

If this tool saved you some headaches, consider buying me a coffee! ☕

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FF813F?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white)](https://buymeacoffee.com/pksmartunew)

## License

MIT License
