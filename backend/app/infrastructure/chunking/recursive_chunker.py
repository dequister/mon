from app.domain.entities import Chunk, DocumentSection
from app.domain.ports import TextChunker

_SEPARATORS = ("\n\n", "\n", ". ", "; ", ", ", " ", "")


class RecursiveTextChunker(TextChunker):
    """Divide o texto pelo separador mais "forte" possível (parágrafo > linha > frase > palavra),
    juntando pedaços até o limite de caracteres e mantendo sobreposição entre chunks."""

    def __init__(self, chunk_size: int = 1200, overlap: int = 200):
        if overlap >= chunk_size:
            raise ValueError("overlap deve ser menor que chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, sections: list[DocumentSection]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for section in sections:
            # Blocos tabulares já vêm dimensionados pelo loader.
            if section.kind == "table" or len(section.text) <= self.chunk_size:
                pieces = [section.text]
            else:
                pieces = self.split_text(section.text)
            for piece in pieces:
                chunks.append(
                    Chunk(
                        text=piece,
                        index=len(chunks),
                        page=section.page,
                        sheet=section.sheet,
                        heading=section.heading,
                        ocr=section.ocr,
                    )
                )
        return chunks

    def split_text(self, text: str) -> list[str]:
        return [piece for piece in self._split(text, _SEPARATORS) if piece.strip()]

    def _split(self, text: str, separators: tuple[str, ...]) -> list[str]:
        separator, remaining = separators[-1], ()
        for i, candidate in enumerate(separators):
            if candidate == "" or candidate in text:
                separator, remaining = candidate, separators[i + 1:]
                break
        parts = text.split(separator) if separator else list(text)

        result: list[str] = []
        fitting: list[str] = []
        for part in parts:
            if len(part) <= self.chunk_size:
                fitting.append(part)
                continue
            if fitting:
                result.extend(self._merge(fitting, separator))
                fitting = []
            # Parte grande demais: desce para o próximo separador.
            result.extend(self._split(part, remaining) if remaining else [part])
        if fitting:
            result.extend(self._merge(fitting, separator))
        return result

    def _merge(self, parts: list[str], separator: str) -> list[str]:
        merged: list[str] = []
        window: list[str] = []
        length = 0
        sep_len = len(separator)
        for part in parts:
            extra = len(part) + (sep_len if window else 0)
            if window and length + extra > self.chunk_size:
                merged.append(separator.join(window).strip())
                # Descarta do início até caber a sobreposição configurada.
                while window and (length > self.overlap or length + extra > self.chunk_size):
                    length -= len(window[0]) + (sep_len if len(window) > 1 else 0)
                    window.pop(0)
                extra = len(part) + (sep_len if window else 0)
            window.append(part)
            length += extra
        if window:
            merged.append(separator.join(window).strip())
        return [m for m in merged if m]
