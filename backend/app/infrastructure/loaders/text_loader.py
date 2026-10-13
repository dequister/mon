import html
import re
from pathlib import Path

from charset_normalizer import from_bytes

from app.domain.entities import DocumentSection, LoadedDocument
from app.infrastructure.loaders.base import BaseLoader

_MD_HEADING = re.compile(r"^#{1,6}\s+(.+)$")


# Codificações usuais em arquivos brasileiros; restringir evita falsos positivos.
_FALLBACK_ENCODINGS = ["cp1252", "latin_1", "cp850", "mac_roman", "utf_16"]


def read_text(path: Path) -> str:
    """Lê texto em UTF-8 ou detecta a codificação legada (CP1252, Latin-1...)."""
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    best = from_bytes(raw, cp_isolation=_FALLBACK_ENCODINGS).best()
    return str(best) if best is not None else raw.decode("cp1252", errors="replace")


class TextLoader(BaseLoader):
    extensions = (".txt", ".md", ".markdown", ".json", ".xml", ".html", ".htm")

    def _extract(self, path: Path) -> LoadedDocument:
        text = read_text(path)
        if path.suffix.lower() in (".md", ".markdown"):
            return LoadedDocument(sections=self._split_markdown(text))
        if path.suffix.lower() in (".html", ".htm", ".xml"):
            text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
            text = html.unescape(re.sub(r"<[^>]+>", " ", text))
        return LoadedDocument(sections=[DocumentSection(text=text)])

    @staticmethod
    def _split_markdown(text: str) -> list[DocumentSection]:
        sections: list[DocumentSection] = []
        heading: str | None = None
        buffer: list[str] = []
        for line in text.splitlines():
            match = _MD_HEADING.match(line)
            if match:
                if buffer:
                    sections.append(DocumentSection(text="\n".join(buffer), heading=heading))
                    buffer = []
                heading = match.group(1).strip()
            buffer.append(line)
        if buffer:
            sections.append(DocumentSection(text="\n".join(buffer), heading=heading))
        return sections
