import io

import pymupdf
from PIL import Image, ImageDraw

from app.infrastructure.ocr.scan_detector import HeuristicScanDetector


def _image_bytes() -> bytes:
    image = Image.new("RGB", (1200, 1600), "white")
    draw = ImageDraw.Draw(image)
    for line in range(30):
        draw.text((80, 80 + line * 45), "Texto digitalizado do edital de matrícula", fill="black")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _mixed_pdf() -> pymupdf.Document:
    pdf = pymupdf.open()
    native = pdf.new_page()
    native.insert_text((72, 72), "Regulamento de estágio supervisionado do curso. " * 3)
    native.insert_text((72, 100), "Artigo 1º O estágio é obrigatório para a conclusão do curso.")
    scanned = pdf.new_page()
    scanned.insert_image(scanned.rect, stream=_image_bytes())
    pdf.new_page()  # página em branco
    hybrid = pdf.new_page()
    hybrid.insert_image(pymupdf.Rect(0, 60, hybrid.rect.width, hybrid.rect.height), stream=_image_bytes())
    hybrid.insert_text((40, 30), "CEFET/RJ - Diretoria de Ensino - Departamento de Engenharia de Produção")
    hybrid.insert_text((40, 45), "Documento digitalizado anexado ao processo administrativo")
    return pdf


def test_detects_each_page_type():
    detector = HeuristicScanDetector()
    pdf = _mixed_pdf()
    results = [detector.analyze(page, page.get_text()) for page in pdf]

    assert results[0].needs_ocr is False and results[0].reason == "texto nativo"
    assert results[1].needs_ocr is True and results[1].image_coverage > 0.9
    assert results[2].needs_ocr is False and results[2].reason == "página em branco"
    assert results[3].needs_ocr is True and "híbrida" in results[3].reason


def test_garbage_ratio_flags_broken_text_layer():
    assert HeuristicScanDetector.garbage_ratio("��� abc") > 0.4
    assert HeuristicScanDetector.garbage_ratio("Texto normal com acentuação.") == 0.0
