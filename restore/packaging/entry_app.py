"""PyInstaller entry point for the Arcalume app window."""
import multiprocessing

from arcana_restore.app.main import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
