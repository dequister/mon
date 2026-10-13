from pathlib import Path

from docx import Document as open_docx
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.domain.entities import DocumentSection, LoadedDocument
from app.infrastructure.loaders.base import BaseLoader

_HEADING_STYLES = ("heading", "título", "titulo", "title")


class DocxLoader(BaseLoader):
    """Lê .docx preservando a ordem de parágrafos e tabelas e agrupando por títulos."""

    extensions = (".docx",)

    def _extract(self, path: Path) -> LoadedDocument:
        document = open_docx(str(path))
        sections: list[DocumentSection] = []
        heading: str | None = None
        buffer: list[str] = []

        def flush() -> None:
            if buffer:
                sections.append(DocumentSection(text="\n".join(buffer), heading=heading))
                buffer.clear()

        for block in document.iter_inner_content():
            if isinstance(block, Paragraph):
                text = block.text.strip()
                if not text:
                    continue
                if self._is_heading(block):
                    flush()
                    heading = text[:200]
                buffer.append(text)
            elif isinstance(block, Table):
                buffer.append(self._table_to_text(block))
        flush()
        title = document.core_properties.title or None
        return LoadedDocument(sections=sections, metadata={"title": title})

    @staticmethod
    def _is_heading(paragraph: Paragraph) -> bool:
        style = (paragraph.style.name if paragraph.style is not None else "").lower()
        return style.startswith(_HEADING_STYLES)

    @staticmethod
    def _table_to_text(table: Table) -> str:
        rows = []
        for row in table.rows:
            cells: list[str] = []
            for cell in row.cells:
                value = " ".join(cell.text.split())
                # Células mescladas se repetem; evita duplicar.
                if not cells or cells[-1] != value:
                    cells.append(value)
            if any(cells):
                rows.append(" | ".join(cells))
        return "\n".join(rows)
