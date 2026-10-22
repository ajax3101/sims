"""Format-neutral report model: a title, meta lines and blocks; every exporter renders the same model."""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

TOTAL_LABEL = "Разом"


@dataclass
class Column:
    key: str
    header: str
    kind: str = "text"  # text | int | money | date


@dataclass
class TableBlock:
    columns: list[Column]
    rows: list[dict[str, Any]]
    totals: list[str] = field(default_factory=list)  # keys of money/int columns summed in a last row
    title: str | None = None

    def total(self, key: str) -> Decimal:
        return sum((Decimal(r[key] or 0) for r in self.rows), Decimal(0))


@dataclass
class KeyValueBlock:
    pairs: list[tuple[str, Any]]
    title: str | None = None


@dataclass
class Document:
    title: str
    blocks: list[TableBlock | KeyValueBlock]
    meta: list[str] = field(default_factory=list)

    @property
    def widest_table(self) -> int:
        return max((len(b.columns) for b in self.blocks if isinstance(b, TableBlock)), default=2)


def money_text(value: Decimal | None) -> str:
    """Ukrainian money format: '12 345,50'."""
    if value is None:
        return ""
    return f"{Decimal(value):,.2f}".replace(",", " ").replace(".", ",")


def cell_text(value: Any, kind: str = "text") -> str:
    if value is None:
        return ""
    if kind == "money":
        return money_text(value)
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    return str(value)
