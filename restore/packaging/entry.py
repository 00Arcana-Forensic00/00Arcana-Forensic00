"""PyInstaller entry point for the arcana-restore single-file executable."""
import multiprocessing

from arcana_restore.cli import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
