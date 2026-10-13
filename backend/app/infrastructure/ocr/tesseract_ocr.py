import pytesseract
from PIL import Image, ImageOps

from app.domain.ports import OcrEngine


class TesseractOcrEngine(OcrEngine):
    """OCR com Tesseract (LSTM), idiomas configuráveis (ex.: por+eng)."""

    def __init__(self, languages: str = "por+eng", page_segmentation_mode: int = 3):
        self.languages = languages
        self.config = f"--oem 1 --psm {page_segmentation_mode}"

    def image_to_text(self, image: Image.Image) -> str:
        # Tons de cinza + autocontraste melhoram o reconhecimento em digitalizações.
        prepared = ImageOps.autocontrast(ImageOps.grayscale(image))
        return pytesseract.image_to_string(prepared, lang=self.languages, config=self.config)
