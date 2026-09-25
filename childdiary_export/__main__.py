"""Main entry point for ChildDiary Export.

This module provides a unified entry point that can be used by:
- Direct execution: python -m childdiary_export
- PyInstaller: as the main script
- Briefcase: as the app entry point

The behavior depends on how it's invoked:
- With --gui flag or no arguments: launches the GUI
- With CLI arguments: runs the CLI version
"""

import sys


def main() -> None:
    """Main entry point that decides between GUI and CLI."""
    # Check if we should launch the GUI
    # This happens when:
    # 1. No arguments are provided
    # 2. --gui flag is provided
    # 3. Running as a frozen bundle (PyInstaller)

    gui_mode = False

    # Check for explicit GUI mode
    if "--gui" in sys.argv:
        sys.argv.remove("--gui")
        gui_mode = True

    # Check for frozen bundle (PyInstaller)
    if getattr(sys, "frozen", False):
        gui_mode = True

    # If no arguments provided and not running as CLI, use GUI
    # CLI arguments start with '-'
    if not gui_mode and len(sys.argv) > 1:
        cli_args = [arg for arg in sys.argv[1:] if arg.startswith("-")]
        if not cli_args:
            gui_mode = True

    if gui_mode:
        # Launch GUI
        try:
            from childdiary_export.gui import main as gui_main

            gui_main()
        except ImportError:
            print("GUI mode requires tkinter. Install it with:")
            print("  macOS: brew install python-tk")
            print("  Windows: usually included with Python")
            print("  Ubuntu: sudo apt-get install python3-tk")
            sys.exit(1)
    else:
        # Launch CLI
        from childdiary_export.cli import main as cli_main

        cli_main()


if __name__ == "__main__":
    main()
