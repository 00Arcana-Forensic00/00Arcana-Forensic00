"""PyInstaller entry point for the windowed Arcana Restore app."""
import multiprocessing

from arcana_restore.gui import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
