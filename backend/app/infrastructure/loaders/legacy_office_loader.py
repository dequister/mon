import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

from app.core.exceptions import ExtractionError
from app.domain.entities import LoadedDocument
from app.domain.ports import DocumentLoader


class LibreOfficeConvertingLoader(DocumentLoader):
    """Adapter: converte formatos legados (.doc, .rtf, .odt, .ppt) com o LibreOffice
    e delega a leitura ao loader do formato moderno."""

    def __init__(self, extensions: tuple[str, ...], target_format: str, delegate: DocumentLoader,
                 soffice_bin: str = "soffice", timeout: int = 180):
        self.extensions = extensions
        self.target_format = target_format
        self.delegate = delegate
        self.soffice_bin = soffice_bin
        self.timeout = timeout

    def load(self, path: Path) -> LoadedDocument:
        if shutil.which(self.soffice_bin) is None:
            raise ExtractionError("LibreOffice não está instalado para converter este formato.")
        with tempfile.TemporaryDirectory() as tmp:
            # Perfil isolado permite conversões em paralelo.
            profile = Path(tmp, f"profile-{uuid.uuid4().hex}").as_uri()
            command = [
                self.soffice_bin, f"-env:UserInstallation={profile}", "--headless",
                "--convert-to", self.target_format, "--outdir", tmp, str(path),
            ]
            try:
                subprocess.run(command, check=True, capture_output=True, timeout=self.timeout)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                raise ExtractionError(f"Falha ao converter {path.name} com o LibreOffice.") from exc
            converted = Path(tmp, f"{path.stem}.{self.target_format}")
            if not converted.exists():
                raise ExtractionError(f"Conversão de {path.name} não gerou arquivo.")
            return self.delegate.load(converted)
