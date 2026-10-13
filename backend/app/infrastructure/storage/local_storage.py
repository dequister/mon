import re
import shutil
from pathlib import Path
from typing import BinaryIO

from app.domain.ports import FileStorage

_UNSAFE = re.compile(r"[^\w.\- ()]+", re.UNICODE)


def safe_filename(filename: str) -> str:
    name = Path(filename).name.strip()
    return _UNSAFE.sub("_", name)[:200] or "arquivo"


class LocalFileStorage(FileStorage):
    """Armazena cada documento em <base>/<document_id>/<arquivo>."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, stream: BinaryIO, document_id: str, filename: str) -> Path:
        folder = self.base_dir / document_id
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True)
        target = folder / safe_filename(filename)
        with target.open("wb") as output:
            shutil.copyfileobj(stream, output, length=1024 * 1024)
        return target

    def delete(self, document_id: str) -> None:
        shutil.rmtree(self.base_dir / document_id, ignore_errors=True)
