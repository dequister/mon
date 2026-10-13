import io
from pathlib import Path

import pandas as pd

from app.domain.entities import DocumentSection, LoadedDocument
from app.infrastructure.loaders.base import BaseLoader
from app.infrastructure.loaders.text_loader import read_text


class SpreadsheetLoader(BaseLoader):
    """Converte cada linha em pares "coluna: valor" e agrupa linhas em blocos.

    O formato chave-valor preserva o significado de cada célula no embedding,
    o que funciona melhor que CSV cru para busca semântica.
    """

    extensions = (".xlsx", ".xlsm", ".xls", ".ods", ".csv", ".tsv")

    def __init__(self, block_chars: int = 1200):
        self.block_chars = block_chars

    def _extract(self, path: Path) -> LoadedDocument:
        sheets = self._read(path)
        sections: list[DocumentSection] = []
        for sheet_name, frame in sheets.items():
            sections.extend(self._frame_to_sections(sheet_name, frame))
        return LoadedDocument(sections=sections, metadata={"sheets": list(sheets.keys())})

    def _read(self, path: Path) -> dict[str, pd.DataFrame]:
        suffix = path.suffix.lower()
        if suffix in (".csv", ".tsv"):
            text = read_text(path)
            sep = "\t" if suffix == ".tsv" else None
            frame = pd.read_csv(
                io.StringIO(text), sep=sep, engine="python", dtype=str, keep_default_na=False
            )
            return {path.stem: frame}
        engine = "odf" if suffix == ".ods" else None
        return pd.read_excel(path, sheet_name=None, dtype=str, engine=engine, keep_default_na=False)

    def _frame_to_sections(self, sheet: str, frame: pd.DataFrame) -> list[DocumentSection]:
        frame = frame.fillna("")
        columns = [self._column_name(col, i) for i, col in enumerate(frame.columns)]
        sections: list[DocumentSection] = []
        lines: list[str] = []
        first_row = 2  # linha 1 é o cabeçalho
        size = 0
        for offset, row in enumerate(frame.itertuples(index=False)):
            pairs = [f"{col}: {str(val).strip()}" for col, val in zip(columns, row) if str(val).strip()]
            if not pairs:
                continue
            line = "; ".join(pairs)
            if lines and size + len(line) > self.block_chars:
                sections.append(self._section(sheet, lines, first_row, offset + 1))
                lines, size, first_row = [], 0, offset + 2
            lines.append(line)
            size += len(line) + 1
        if lines:
            sections.append(self._section(sheet, lines, first_row, len(frame) + 1))
        return sections

    @staticmethod
    def _section(sheet: str, lines: list[str], start: int, end: int) -> DocumentSection:
        heading = f"Planilha {sheet} (linhas {start}-{end})"
        return DocumentSection(text="\n".join(lines), sheet=sheet, heading=heading, kind="table")

    @staticmethod
    def _column_name(column, index: int) -> str:
        name = str(column).strip()
        return f"Coluna {index + 1}" if not name or name.startswith("Unnamed") else name
