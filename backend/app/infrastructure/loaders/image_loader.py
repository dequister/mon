from pathlib import Path

from PIL import Image, ImageSequence

from app.domain.entities import DocumentSection, LoadedDocument
from app.domain.ports import OcrEngine
from app.infrastructure.loaders.base import BaseLoader


class ImageLoader(BaseLoader):
    """Imagens digitalizadas: OCR em cada quadro (TIFF pode ter várias páginas)."""

    extensions = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp")

    def __init__(self, ocr: OcrEngine):
        self.ocr = ocr

    def _extract(self, path: Path) -> LoadedDocument:
        sections: list[DocumentSection] = []
        with Image.open(path) as image:
            for number, frame in enumerate(ImageSequence.Iterator(image), start=1):
                text = self.ocr.image_to_text(frame.convert("RGB"))
                sections.append(DocumentSection(text=text, page=number, ocr=True))
        return LoadedDocument(sections=sections, page_count=len(sections), ocr_pages=len(sections))
