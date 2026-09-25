"""Main entry point for ChildDiary Export.

This module provides a unified entry point that can be used by:
- Direct execution: python -m .
- PyInstaller: as the main script
- Briefcase: as the app entry point

This redirects to the childdiary_export package.
"""

from childdiary_export.__main__ import main

if __name__ == "__main__":
    main()
