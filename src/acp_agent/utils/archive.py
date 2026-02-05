from __future__ import annotations

import shutil
import tarfile
import zipfile
from pathlib import Path


def extract_binary(
    archive_path: Path | str, binary_name: str, dest_dir: Path | str
) -> Path:
    """Extract a binary from an archive or copy it if not an archive."""
    archive_path = Path(archive_path)
    dest_dir = Path(dest_dir)
    dest_path = dest_dir / binary_name

    archive_str = str(archive_path)
    if archive_str.endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extract(binary_name, path=dest_dir)
    elif archive_str.endswith((".tar.gz", ".tgz")):
        with tarfile.open(archive_path, "r:gz") as tar_ref:
            tar_ref.extract(binary_name, path=dest_dir)
    else:
        shutil.copy(archive_path, dest_path)

    return dest_path
