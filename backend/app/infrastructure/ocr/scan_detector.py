"""Detecção de páginas escaneadas em PDFs.

Cada página é analisada individualmente, então um PDF misto (parte digital,
parte digitalizada) só recebe OCR onde for necessário.
"""

import unicodedata
from abc import ABC, abstractmethod

import pymupdf

from app.domain.entities import PageAnalysis


class ScanDetector(ABC):
    @abstractmethod
    def analyze(self, page: pymupdf.Page, native_text: str) -> PageAnalysis: ...


class HeuristicScanDetector(ScanDetector):
    """Combina densidade de texto, cobertura de imagens e texto corrompido."""

    def __init__(
        self,
        min_text_chars: int = 50,
        image_coverage_threshold: float = 0.5,
        hybrid_max_chars: int = 400,
        garbage_threshold: float = 0.3,
        vector_drawings_threshold: int = 300,
    ):
        self.min_text_chars = min_text_chars
        self.image_coverage_threshold = image_coverage_threshold
        self.hybrid_max_chars = hybrid_max_chars
        self.garbage_threshold = garbage_threshold
        self.vector_drawings_threshold = vector_drawings_threshold

    def analyze(self, page: pymupdf.Page, native_text: str) -> PageAnalysis:
        stripped = native_text.strip()
        chars = len(stripped)
        coverage = self.image_coverage(page)
        garbage = self.garbage_ratio(stripped)

        def result(needs_ocr: bool, reason: str) -> PageAnalysis:
            return PageAnalysis(needs_ocr, reason, chars, round(coverage, 3), round(garbage, 3))

        # 1) Camada de texto existe, mas está corrompida (fontes sem mapeamento Unicode).
        if chars and garbage >= self.garbage_threshold:
            return result(True, "camada de texto corrompida")
        # 2) Quase nenhum texto e há imagem na página: digitalização típica.
        if chars < self.min_text_chars and coverage > 0.05:
            return result(True, "página escaneada (imagem sem texto)")
        # 3) Página dominada por imagem com pouco texto (ex.: só carimbo ou cabeçalho digital).
        if coverage >= self.image_coverage_threshold and chars < self.hybrid_max_chars:
            return result(True, "página híbrida (imagem predominante)")
        # 4) Texto convertido em curvas vetoriais (sem imagem e sem texto extraível).
        if chars < self.min_text_chars and len(page.get_drawings()) >= self.vector_drawings_threshold:
            return result(True, "texto vetorizado")
        if chars == 0:
            return result(False, "página em branco")
        return result(False, "texto nativo")

    @staticmethod
    def image_coverage(page: pymupdf.Page) -> float:
        """Fração da área da página ocupada por imagens."""
        page_rect = page.rect
        page_area = page_rect.width * page_rect.height
        if page_area <= 0:
            return 0.0
        covered = 0.0
        for info in page.get_image_info():
            bbox = pymupdf.Rect(info["bbox"]) & page_rect
            if not bbox.is_empty:
                covered += bbox.width * bbox.height
        return min(covered / page_area, 1.0)

    @staticmethod
    def garbage_ratio(text: str) -> float:
        """Proporção de caracteres inválidos (substituição, controle, uso privado)."""
        if not text:
            return 0.0
        bad = 0
        for char in text:
            if char in "\n\r\t ":
                continue
            category = unicodedata.category(char)
            if char == "�" or category in ("Cc", "Co", "Cs", "Cn"):
                bad += 1
        visible = sum(1 for c in text if not c.isspace())
        return bad / visible if visible else 0.0
