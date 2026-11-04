"""
Backup Original Image Dataset
Creates a full byte-for-byte backup of data/image_model_dataset before any cleaning or quarantine.
"""
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "data" / "image_model_dataset"
BACKUP_DIR = BASE_DIR / "data" / "image_model_dataset_backup"


def main():
    if not SRC_DIR.exists():
        print(f"ERROR: Source dataset directory not found: {SRC_DIR}")
        sys.exit(1)

    if BACKUP_DIR.exists():
        file_count = len(list(BACKUP_DIR.glob("**/*.*")))
        print(f"Backup already exists at: {BACKUP_DIR}")
        print(f"Total backup files: {file_count}")
        return

    print(f"Creating full backup from: {SRC_DIR}")
    print(f"                     to: {BACKUP_DIR}")
    shutil.copytree(SRC_DIR, BACKUP_DIR)
    file_count = len(list(BACKUP_DIR.glob("**/*.*")))
    print(f"Backup completed successfully! Total files in backup: {file_count}")


if __name__ == "__main__":
    main()
