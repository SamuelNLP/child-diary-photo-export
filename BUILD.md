# Building ChildDiary Export for Non-Technical Users

This document describes how to package the ChildDiary Export script so that non-technical users can run it easily on macOS and Windows.

## Overview

The project now includes three approaches to make the script accessible to non-technical users:

1. **PyInstaller** - Creates standalone executables (single `.exe` or binary)
2. **Briefcase** - Creates native app bundles (`.app` on macOS, `.msi` installer on Windows)
3. **GUI Wrapper** - A Tkinter-based graphical interface

## Files Created

```
child-diary-photo-export/
├── childdiary_export/     # Python package
│   ├── __init__.py        # Package init
│   ├── cli.py             # CLI script (formerly script.py)
│   ├── auth.py            # Authentication module
│   ├── gui.py             # Tkinter GUI wrapper
│   └── __main__.py        # Unified entry point (CLI + GUI)
├── build_script.py        # Build automation script
├── ChildDiaryExport.spec          # NEW: PyInstaller spec (CLI)
├── ChildDiaryExport-GUI.spec      # NEW: PyInstaller spec (GUI)
├── briefcase.toml         # NEW: Briefcase configuration
├── resources/             # NEW: Directory for icons, images
│   └── .gitkeep
├── Makefile              # UPDATED: Added build commands
└── .gitignore            # UPDATED: Added build artifact patterns
```

## Quick Start

### Prerequisites

- Python 3.14+
- uv package manager (already in use by the project)

### Install Build Tools

```bash
# Install PyInstaller for standalone executables
uv pip install pyinstaller

# Install Briefcase for native app bundles (optional)
uv pip install briefcase
```

---

## Option 1: PyInstaller (Recommended for Quick Distribution)

Creates standalone executables that users can double-click.

### Build CLI Version

```bash
# Using the build script
python build.py pyinstaller

# Or directly with PyInstaller
uv run pyinstaller --onefile --name ChildDiaryExport-CLI --console -m childdiary_export
```

Output: `dist/ChildDiaryExport-CLI` (macOS) or `dist/ChildDiaryExport-CLI.exe` (Windows)

### Build GUI Version

```bash
# Using the build script
python build.py pyinstaller-gui

# Or directly with PyInstaller
uv run pyinstaller --onefile --name ChildDiaryExport --windowed -m childdiary_export --gui
```

Output: `dist/ChildDiaryExport` (macOS) or `dist/ChildDiaryExport.exe` (Windows)

### PyInstaller Notes

- **`--onefile`**: Bundles everything into a single executable
- **`--console`**: Shows terminal window (for CLI)
- **`--windowed`**: No terminal window (for GUI)
- **`--icon`**: Add custom icons (place in `resources/`)
  - macOS: `resources/icon.icns` (1024x1024)
  - Windows: `resources/icon.ico` (multiple sizes)

### Cross-Platform Building

**Important:** PyInstaller executables must be built on the target platform.

- Build macOS executable on a Mac
- Build Windows executable on Windows

For cross-compilation, you'd need to set up cross-platform build environments.

---

## Option 2: Briefcase (Recommended for Polished Distribution)

Creates native application bundles with proper icons, metadata, and installers.

### Build for macOS

```bash
# Using the build script
python build.py briefcase

# Or manually
uv run briefcase create macos
uv run briefcase build macos
uv run briefcase run macos
```

Output: A native `.app` bundle that can be dragged to Applications folder.

### Build for Windows

```bash
uv run briefcase create windows
uv run briefcase build windows
uv run briefcase run windows
```

Output: An `.msi` installer file.

### Briefcase Configuration

The Briefcase configuration is in `pyproject.toml` under `[tool.briefcase]`:

```toml
[tool.briefcase]
project_name = "ChildDiary Export"
package_name = "childdiary_export"
bundle_identifier = "net.childdiary.export"
version = "1.0.0"
requires_python = ">=3.14"
supported_platforms = ["macos", "windows"]

[tool.briefcase.app.childdiary_export]
entry_point = "gui:main"
icon = "resources/icon"
requires_network = true
```

### Briefcase Notes

- Creates proper macOS `.app` bundles with icon, Info.plist, etc.
- Creates Windows installers with Start Menu entries
- Handles Python runtime bundling automatically
- Supports code signing for distribution

---

## Option 3: GUI Wrapper (Simplest for Development)

The `childdiary_export/gui.py` file provides a simple Tkinter interface for the CLI.

### Run GUI Directly

```bash
uv run python -m childdiary_export --gui
```

Or through the unified entry point:

```bash
uv run python -m childdiary_export
```

### GUI Features

- **Output Directory**: Browse button to select where to save files
- **Compression**: Dropdown for zip/gzip/bz2 options
- **Start Page**: Numeric input for resuming downloads
- **Status Bar**: Shows current operation state
- **Output Log**: Real-time display of script output
- **Start/Stop Buttons**: Control the export process

### Screenshot (Conceptual)

```
+------------------------------------------+
| ChildDiary Photo Export                  |
|                                          |
| Output Directory: [_________] [Browse]   |
|                                          |
| Compression: [zip ▼]                      |
| (Leave empty for no compression)         |
|                                          |
| Start Page: [1]                          |
|                                          |
| [Start Export] [Stop]                    |
|                                          |
| Status: Ready                           |
|                                          |
| +--------------------------------------+ |
| | Output log area...                   | |
| |                                      | |
| +--------------------------------------+ |
+------------------------------------------+
```

---

## Build Automation

The `build.py` script provides a unified interface:

```bash
# Show help
python build_script.py

# Build CLI with PyInstaller
python build_script.py pyinstaller

# Build GUI with PyInstaller
python build_script.py pyinstaller-gui

# Build with Briefcase
python build_script.py briefcase

# Build everything
python build_script.py all

# Clean build artifacts
python build_script.py clean
```

Or use Make commands:

```bash
make build-cli      # Build CLI with PyInstaller
make build-gui      # Build GUI with PyInstaller
make build          # Build both with PyInstaller
make build-briefcase # Build with Briefcase
make clean-build    # Clean build artifacts
```

---

## Adding Icons

To give your app a professional look, add icons to the `resources/` directory:

### macOS

1. Create an `.icns` file (1024x1024 recommended)
2. Save as `resources/icon.icns`

To create an `.icns` file:
```bash
# Using img2icns (macOS)
brew install img2icns
img2icns -i icon.png -o resources/icon.icns

# Or use online tools like https://iconverticons.com/
```

### Windows

1. Create an `.ico` file with multiple sizes (256, 48, 32, 16)
2. Save as `resources/icon.ico`

To create an `.ico` file:
```bash
# Using ImageMagick
convert icon.png -define icon:auto-resize=256,48,32,16 resources/icon.ico

# Or use online tools
```

### DMG Background (macOS Briefcase)

For Briefcase DMG builds, add a background image:
- Create a PNG image (e.g., 600x400)
- Save as `resources/dmg_background.png`

---

## Distribution

### PyInstaller Executables

1. Build the executable for each platform
2. Test on a clean machine (no Python installed)
3. Package in a zip file or create an installer

**Example for Windows:**
```
ChildDiaryExport-1.0.0-windows.zip
├── ChildDiaryExport.exe
├── README.txt
└── .env.example
```

**Example for macOS:**
```
ChildDiaryExport-1.0.0-macos.zip
├── ChildDiaryExport
├── README.txt
└── .env.example
```

### Briefcase Bundles

Briefcase creates platform-specific distributables:

- **macOS**: `.dmg` file (e.g., `ChildDiaryExport-1.0.0.dmg`)
- **Windows**: `.msi` installer (e.g., `ChildDiaryExport-1.0.0.msi`)

These are ready for distribution to users.

---

## User Instructions

### For CLI Executable Users

1. Download the executable for your platform
2. Double-click to run
3. You'll see a terminal window with instructions
4. Create a `.env` file or use keyring for credentials
5. Run with flags: `-c zip -o ./photos -p 1`

### For GUI Executable Users

1. Download the executable for your platform
2. Double-click to run
3. A window will appear with options
4. Select output directory using Browse button
5. Choose compression option (optional)
6. Enter start page (default: 1)
7. Click "Start Export"
8. Watch progress in the output log
9. Credentials will be prompted and saved securely

### For Briefcase App Users

**macOS:**
1. Download the `.dmg` file
2. Open it and drag the app to Applications
3. Run from Applications folder

**Windows:**
1. Download the `.msi` installer
2. Double-click to run installer
3. Follow installer prompts
4. Run from Start Menu

---

## Troubleshooting

### Common Issues

#### Tkinter not available

On some Python installations, Tkinter is not included.

**macOS:**
```bash
brew install python-tk
```

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**Windows:** Usually included with Python installer.

#### PyInstaller: ModuleNotFoundError

Add missing imports to the spec file's `hiddenimports` list.

#### PyInstaller: Executable too large

The onefile executable includes all dependencies. To reduce size:
- Use `upx=True` in spec file (compresses executable)
- Use `--exclude-module` for unused modules
- Build on the target platform

#### Briefcase: Missing dependencies

Briefcase automatically handles most dependencies. If you have custom ones, add them to `briefcase.toml`:

```toml
[tool.briefcase.build.childdiary_export]
requires = [
    "keyring>=25.0.0",
    "requests>=2.32.5",
    # Add your custom dependencies here
]
```

---

## Advanced: Customizing the GUI

The GUI in `gui.py` can be customized:

- **Theme**: Use `ttk` themes for different looks
- **Icons**: Add custom icons for buttons
- **Additional Options**: Add more CLI flags as GUI controls
- **Progress Bar**: Add a progress bar for download status
- **Credentials**: Add a credentials tab for first-time setup

Example of adding a theme:

```python
style = ttk.Style()
style.theme_use("clam")  # or 'alt', 'default', 'classic'
```

---

## Advanced: Creating a Proper Package

For wider distribution, consider creating a Python package:

1. Create a `src/` directory
2. Move your code into `src/childdiary_export/`
3. Add `__init__.py` files
4. Update imports to use relative imports
5. Publish to PyPI or create wheels

This allows users to install with `pip install childdiary-export` or `uv pip install childdiary-export`.

---

## Summary

| Method | Ease | Output | Platform | Best For |
|--------|------|--------|----------|----------|
| PyInstaller CLI | ⭐⭐⭐⭐ | Executable | Both | Quick testing |
| PyInstaller GUI | ⭐⭐⭐⭐ | Executable | Both | Simple distribution |
| Briefcase | ⭐⭐⭐ | Native App | Both | Polished distribution |
| GUI Wrapper | ⭐⭐⭐⭐⭐ | Python script | Both | Development |

**Recommendation:** Start with PyInstaller GUI for quick testing, then use Briefcase for final distribution.
