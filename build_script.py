#!/usr/bin/env python3
"""Build script for ChildDiary Export.

This script provides a unified interface for building the application
with different tools:
- PyInstaller: for standalone executables
- Briefcase: for native app bundles

Usage:
    python build.py pyinstaller    # Build with PyInstaller
    python build.py pyinstaller-gui # Build GUI with PyInstaller
    python build.py briefcase      # Build with Briefcase
    python build.py all            # Build with all methods
    python build.py clean          # Clean build artifacts
"""

import shutil
import subprocess
import sys
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"


def run_command(cmd: list[str], cwd: Path | None = None) -> bool:
    """Run a shell command and return True if successful.

    Parameters
    ----------
    cmd : list[str]
        Command to run as a list of arguments.
    cwd : Path | None
        Working directory for the command.

    Returns
    -------
    bool
        True if the command succeeded (return code 0).
    """
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=False,
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True,
        )
        return result.returncode == 0
    except KeyboardInterrupt:
        print("Build cancelled by user")
        return False


def clean() -> bool:
    """Clean build artifacts."""
    print("Cleaning build artifacts...")

    success = True

    # Remove build directory
    if BUILD_DIR.exists():
        print(f"Removing {BUILD_DIR}")
        shutil.rmtree(BUILD_DIR, ignore_errors=True)

    # Remove dist directory
    if DIST_DIR.exists():
        print(f"Removing {DIST_DIR}")
        shutil.rmtree(DIST_DIR, ignore_errors=True)

    # Remove PyInstaller spec files
    for spec_file in PROJECT_ROOT.glob("*.spec"):
        print(f"Removing {spec_file}")
        spec_file.unlink(missing_ok=True)

    # Remove __pycache__ directories
    for pycache in PROJECT_ROOT.rglob("__pycache__"):
        print(f"Removing {pycache}")
        shutil.rmtree(pycache, ignore_errors=True)

    # Remove .pyc files
    for pyc in PROJECT_ROOT.rglob("*.pyc"):
        print(f"Removing {pyc}")
        pyc.unlink(missing_ok=True)

    print("Clean complete")
    return success


def build_pyinstaller_cli() -> bool:
    """Build CLI version with PyInstaller."""
    print("\n" + "=" * 60)
    print("Building CLI version with PyInstaller")
    print("=" * 60)

    # Create output directories
    BUILD_DIR.mkdir(exist_ok=True)
    DIST_DIR.mkdir(exist_ok=True)

    # Build with PyInstaller
    cmd = [
        sys.executable,
        "-m",
        "pyinstaller",
        "--onefile",
        "--name",
        "ChildDiaryExport-CLI",
        "--console",  # Show console for CLI
        "--clean",
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
        "--add-data",
        ".env.example:.",
        "--add-data",
        "README.md:.",
        "--hidden-import",
        "keyring",
        "--hidden-import",
        "tenacity",
        "-m",
        "childdiary_export.script",
    ]

    return run_command(cmd, cwd=PROJECT_ROOT)


def build_pyinstaller_gui() -> bool:
    """Build GUI version with PyInstaller."""
    print("\n" + "=" * 60)
    print("Building GUI version with PyInstaller")
    print("=" * 60)

    # Create output directories
    BUILD_DIR.mkdir(exist_ok=True)
    DIST_DIR.mkdir(exist_ok=True)

    # Check for icon files
    icon_files = []
    if (PROJECT_ROOT / "resources" / "icon.ico").exists():
        icon_files.append("--icon=resources/icon.ico")
    if (PROJECT_ROOT / "resources" / "icon.icns").exists():
        icon_files.append("--icon=resources/icon.icns")

    # Build with PyInstaller
    cmd = (
        [
            sys.executable,
            "-m",
            "pyinstaller",
            "--onefile",
            "--name",
            "ChildDiaryExport",
            "--windowed",  # No console for GUI
            "--clean",
            "--distpath",
            str(DIST_DIR),
            "--workpath",
            str(BUILD_DIR),
            "--add-data",
            ".env.example:.",
            "--add-data",
            "README.md:.",
            "--hidden-import",
            "keyring",
            "--hidden-import",
            "tenacity",
            "--hidden-import",
            "tkinter",
            "--hidden-import",
            "tkinter.ttk",
            "--hidden-import",
            "tkinter.filedialog",
            "--hidden-import",
            "tkinter.messagebox",
        ]
        + icon_files
        + ["-m", "childdiary_export.gui"]
    )

    return run_command(cmd, cwd=PROJECT_ROOT)


def build_briefcase() -> bool:
    """Build with Briefcase."""
    print("\n" + "=" * 60)
    print("Building with Briefcase")
    print("=" * 60)

    # Check if briefcase is installed
    try:
        import briefcase  # noqa: F401
    except ImportError:
        print("Briefcase is not installed. Installing...")
        if not run_command([sys.executable, "-m", "pip", "install", "briefcase"]):
            print("Failed to install briefcase")
            return False

    # Briefcase commands
    commands = [
        [sys.executable, "-m", "briefcase", "create"],
        [sys.executable, "-m", "briefcase", "build"],
        [sys.executable, "-m", "briefcase", "run"],
    ]

    all_success = True
    for cmd in commands:
        if not run_command(cmd, cwd=PROJECT_ROOT):
            all_success = False
            break

    return all_success


def build_all() -> bool:
    """Build with all methods."""
    print("\n" + "=" * 60)
    print("Building with all methods")
    print("=" * 60)

    all_success = True

    # Clean first
    clean()

    # Build CLI with PyInstaller
    if not build_pyinstaller_cli():
        all_success = False

    # Build GUI with PyInstaller
    if not build_pyinstaller_gui():
        all_success = False

    # Build with Briefcase
    if not build_briefcase():
        all_success = False

    return all_success


def print_usage() -> None:
    """Print usage information."""
    print("\n" + "=" * 60)
    print("ChildDiary Export Build Script")
    print("=" * 60)
    print()
    print("Usage:")
    print("    python build.py pyinstaller    # Build CLI with PyInstaller")
    print("    python build.py pyinstaller-gui # Build GUI with PyInstaller")
    print("    python build.py briefcase      # Build with Briefcase")
    print("    python build.py all            # Build with all methods")
    print("    python build.py clean          # Clean build artifacts")
    print("    python build.py               # Show this help")
    print()
    print("Build outputs will be in the 'dist/' directory")
    print("=" * 60)


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1].lower()

    if command == "clean":
        success = clean()
        sys.exit(0 if success else 1)
    elif command == "pyinstaller":
        success = build_pyinstaller_cli()
        sys.exit(0 if success else 1)
    elif command == "pyinstaller-gui":
        success = build_pyinstaller_gui()
        sys.exit(0 if success else 1)
    elif command == "briefcase":
        success = build_briefcase()
        sys.exit(0 if success else 1)
    elif command == "all":
        success = build_all()
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
