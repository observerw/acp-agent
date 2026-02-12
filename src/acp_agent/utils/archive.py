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
    dest_dir.mkdir(parents=True, exist_ok=True)

    if zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            for member in zip_ref.infolist():
                if member.is_dir():
                    continue
                if Path(member.filename).name != binary_name:
                    continue

                with (
                    zip_ref.open(member, "r") as source,
                    dest_path.open("wb") as target,
                ):
                    shutil.copyfileobj(source, target)
                return dest_path

        raise FileNotFoundError(
            f"Binary '{binary_name}' not found in ZIP archive '{archive_path}'"
        )

    if tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path, "r:*") as tar_ref:
            for member in tar_ref.getmembers():
                if not member.isfile():
                    continue
                if Path(member.name).name != binary_name:
                    continue

                source = tar_ref.extractfile(member)
                if source is None:
                    continue
                with source, dest_path.open("wb") as target:
                    shutil.copyfileobj(source, target)
                return dest_path

        raise FileNotFoundError(
            f"Binary '{binary_name}' not found in TAR archive '{archive_path}'"
        )

    shutil.copy(archive_path, dest_path)

    return dest_path
