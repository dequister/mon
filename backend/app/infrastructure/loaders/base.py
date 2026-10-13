import re
import unicodedata
from abc import abstractmethod
from pathlib import Path

from app.core.exceptions import ExtractionError
from app.domain.entities import DocumentSection, LoadedDocument
from app.domain.ports import DocumentLoader

_HYPHEN_BREAK = re.compile(r"(\w)-\n(\w)")
_SPACES = re.compile(r"[ \t ]+")
_BLANK_LINES = re.compile(r"\n{3,}")


class BaseLoader(DocumentLoader):
    """Template Method: extrai, normaliza e descarta seções vazias."""

    extensions: tuple[str, ...] = ()

    def load(self, path: Path) -> LoadedDocument:
        try:
            document = self._extract(path)
        except ExtractionError:
            raise
        except Exception as exc:
            raise ExtractionError(f"Falha ao ler {path.name}: {exc}") from exc
        sections = []
        for section in document.sections:
            section.text = self.normalize(section.text)
            if section.text:
                sections.append(section)
        document.sections = sections
        return document

    @abstractmethod
    def _extract(self, path: Path) -> LoadedDocument: ...

    @staticmethod
    def normalize(text: str) -> str:
        text = unicodedata.normalize("NFC", text).replace("\x00", "")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = _HYPHEN_BREAK.sub(r"\1\2", text)
        text = _SPACES.sub(" ", text)
        text = "\n".join(line.strip() for line in text.split("\n"))
        return _BLANK_LINES.sub("\n\n", text).strip()


def single_section(text: str, **kwargs) -> LoadedDocument:
    return LoadedDocument(sections=[DocumentSection(text=text, **kwargs)])
