import logging
from pathlib import Path

import pymupdf
from PIL import Image

from app.domain.entities import DocumentSection, LoadedDocument
from app.domain.ports import OcrEngine
from app.infrastructure.loaders.base import BaseLoader
from app.infrastructure.ocr.scan_detector import ScanDetector

logger = logging.getLogger(__name__)


class PdfLoader(BaseLoader):
    """Extrai texto nativo e aplica OCR apenas nas páginas detectadas como escaneadas."""

    extensions = (".pdf",)

    def __init__(self, ocr: OcrEngine, detector: ScanDetector, dpi: int = 300):
        self.ocr = ocr
        self.detector = detector
        self.dpi = dpi

    def _extract(self, path: Path) -> LoadedDocument:
        sections: list[DocumentSection] = []
        pages_report: list[dict] = []
        ocr_pages = 0
        with pymupdf.open(path) as pdf:
            for number, page in enumerate(pdf, start=1):
                native = page.get_text("text", sort=True)
                analysis = self.detector.analyze(page, native)
                text, used_ocr = native, False
                if analysis.needs_ocr:
                    ocr_text = self._ocr_page(page)
                    # Mantém o texto mais completo entre nativo e OCR.
                    if len(ocr_text.strip()) > len(native.strip()):
                        text, used_ocr = ocr_text, True
                        ocr_pages += 1
                pages_report.append(
                    {
                        "page": number,
                        "ocr": used_ocr,
                        "reason": analysis.reason,
                        "text_chars": analysis.text_chars,
                        "image_coverage": analysis.image_coverage,
                    }
                )
                sections.append(DocumentSection(text=text, page=number, ocr=used_ocr))
            page_count = pdf.page_count
            title = (pdf.metadata or {}).get("title") or None
        logger.info("%s: %s páginas, %s com OCR.", path.name, page_count, ocr_pages)
        return LoadedDocument(
            sections=sections,
            page_count=page_count,
            ocr_pages=ocr_pages,
            metadata={"title": title, "pages": pages_report},
        )

    def _ocr_page(self, page: pymupdf.Page) -> str:
        pixmap = page.get_pixmap(dpi=self.dpi, alpha=False)
        image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
        return self.ocr.image_to_text(image)
