English | [**日本語**](README.md)

# DeskShelf

> Your desktop, always within reach — even when buried under windows.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6)

DeskShelf is a floating launcher that displays your desktop shortcuts and files in a small always-on-top window. No more minimizing everything just to reach your desktop icons.

No cloud. No tracking. All data stays local.

---

## Features

| Feature | Description |
|---------|-------------|
| **Desktop icon display** | Automatically reads .lnk / .url / .exe from Desktop + Public Desktop |
| **One-click launch** | Click to launch apps/URLs. Tracks usage count and last used time |
| **Always on Top** | Toggle floating above all windows |
| **Star rating** | 0-3 star importance rating. Frequently used apps rise to the top |
| **Auto-sort** | Sorted by stars → last used → name |
| **Tag management** | Create, delete, assign tags. Filter by tag tabs |
| **Dark / Light theme** | One-click toggle. Preference saved automatically |
| **JA / EN language toggle** | Switch UI language with a segment control |
| **Collapsible list** | Shows top 30 items, expand to see the rest |
| **Multi-monitor support** | Window position saved and restored. Falls back if out of bounds |
| **Auto icon extraction** | Extracts icons from .lnk / .exe via Win32 API + PIL |
| **Custom app icon** | Shelf-themed icon for the title bar and taskbar |

---

## Quick Start

### 1. Download & install

**Using git:**
```bash
git clone https://github.com/MiraQue/DeskShelf.git
cd DeskShelf
pip install -r requirements.txt
```

**Without git:**
1. Download the [ZIP file](https://github.com/MiraQue/DeskShelf/archive/refs/heads/master.zip)
2. Extract it and open a terminal in the folder
3. Run `pip install -r requirements.txt`

> Requires Python 3.9+ and Windows 10/11.

### 2. Run

```bash
python main.py
```

Your desktop shortcuts are automatically loaded into a floating window.

### 3. Usage

- Click an icon → launches the app/URL
- Click stars → set importance (0-3 levels)
- Use tag tabs to filter, Tag button to manage tags

---

## Project Structure

```
DeskShelf/
├── main.py              # Entry point (AppUserModelID setup)
├── app.py               # Main window (CustomTkinter)
├── desktop_reader.py    # Desktop shortcut scanner
├── icon_extractor.py    # Win32 API icon extraction
├── launcher.py          # App launch handler
├── config.py            # Settings read/write
├── generate_icon.py     # App icon generator
├── requirements.txt     # Python dependencies
└── data/
    ├── deskshelf.ico    # App icon (.ico)
    └── deskshelf.png    # App icon (.png)

User data: %APPDATA%\DeskShelf\
├── config.json          # User settings (auto-created on first run)
└── cache/icons/         # Extracted icon cache
```

---

## Tech Stack

- **Language**: Python 3.9+
- **GUI**: CustomTkinter (modern UI with Always on Top support)
- **Icon extraction**: ctypes (shell32/gdi32) + PIL (64-bit safe)
- **Shortcut parsing**: win32com (.lnk target and icon info)
- **Settings**: Local JSON file

---

## Requirements

| Item | Requirement |
|------|-------------|
| OS | Windows 10 / 11 |
| Python | 3.9+ |
| Dependencies | customtkinter, pywin32, Pillow |

> Windows only. Uses Windows APIs for desktop shortcut reading and icon extraction.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
