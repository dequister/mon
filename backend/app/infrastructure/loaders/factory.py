from pathlib import Path

from app.core.exceptions import UnsupportedFileTypeError
from app.domain.ports import DocumentLoader, OcrEngine
from app.infrastructure.loaders.docx_loader import DocxLoader
from app.infrastructure.loaders.image_loader import ImageLoader
from app.infrastructure.loaders.legacy_office_loader import LibreOfficeConvertingLoader
from app.infrastructure.loaders.pdf_loader import PdfLoader
from app.infrastructure.loaders.pptx_loader import PptxLoader
from app.infrastructure.loaders.spreadsheet_loader import SpreadsheetLoader
from app.infrastructure.loaders.text_loader import TextLoader
from app.infrastructure.ocr.scan_detector import ScanDetector


class LoaderFactory:
    """Factory/Registry: escolhe o loader (Strategy) pela extensão do arquivo."""

    def __init__(self, loaders: list[DocumentLoader]):
        self._registry: dict[str, DocumentLoader] = {}
        for loader in loaders:
            for extension in loader.extensions:
                self._registry[extension] = loader

    @property
    def supported_extensions(self) -> list[str]:
        return sorted(self._registry)

    def supports(self, filename: str) -> bool:
        return Path(filename).suffix.lower() in self._registry

    def for_path(self, path: Path) -> DocumentLoader:
        loader = self._registry.get(path.suffix.lower())
        if loader is None:
            raise UnsupportedFileTypeError(f"Tipo de arquivo não suportado: {path.suffix or path.name}")
        return loader

    @classmethod
    def default(cls, ocr: OcrEngine, detector: ScanDetector, ocr_dpi: int, soffice_bin: str) -> "LoaderFactory":
        docx, pptx = DocxLoader(), PptxLoader()
        return cls([
            PdfLoader(ocr, detector, ocr_dpi),
            docx,
            pptx,
            SpreadsheetLoader(),
            TextLoader(),
            ImageLoader(ocr),
            LibreOfficeConvertingLoader((".doc", ".rtf", ".odt"), "docx", docx, soffice_bin),
            LibreOfficeConvertingLoader((".ppt", ".odp"), "pptx", pptx, soffice_bin),
        ])
