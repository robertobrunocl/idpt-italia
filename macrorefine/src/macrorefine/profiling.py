"""Profiling: diagnostica automatica delle criticità di un Dataset."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from macrorefine.dataset import Dataset


_SNAKE_CASE_RE = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")


def _is_snake_case(name: str) -> bool:
    return bool(_SNAKE_CASE_RE.match(name))


@dataclass
class ProfileReport:
    """Report strutturato della diagnostica."""

    n_rows: int = 0
    n_cols: int = 0
    non_snake_case_columns: list[str] = field(default_factory=list)
    duplicated_column_names: list[str] = field(default_factory=list)
    empty_columns: list[str] = field(default_factory=list)
    high_null_columns: dict[str, float] = field(default_factory=dict)
    duplicate_rows: int = 0
    dtypes: dict[str, str] = field(default_factory=dict)

    def __repr__(self) -> str:
        lines = [
            "ProfileReport",
            "=" * 40,
            f"Rows: {self.n_rows}   Cols: {self.n_cols}",
            "",
        ]

        if self.non_snake_case_columns:
            lines.append(f"⚠ Non-snake_case columns ({len(self.non_snake_case_columns)}):")
            for c in self.non_snake_case_columns:
                lines.append(f"    - {c!r}")

        if self.duplicated_column_names:
            lines.append(f"⚠ Duplicated column names: {self.duplicated_column_names}")

        if self.empty_columns:
            lines.append(f"⚠ Empty columns: {self.empty_columns}")

        if self.high_null_columns:
            lines.append("⚠ High-null columns (>50%):")
            for col, ratio in self.high_null_columns.items():
                lines.append(f"    - {col}: {ratio:.1%} null")

        if self.duplicate_rows:
            lines.append(f"⚠ Duplicate rows: {self.duplicate_rows}")

        lines.append("")
        lines.append("Dtypes:")
        for col, dt in self.dtypes.items():
            lines.append(f"    {col}: {dt}")

        return "\n".join(lines)


def profile(dataset: "Dataset", high_null_threshold: float = 0.5) -> ProfileReport:
    """Calcola il ProfileReport per un Dataset.

    Args:
        dataset: Dataset da analizzare.
        high_null_threshold: soglia (0-1) sopra la quale una colonna è
            considerata ad alto contenuto di null.
    """
    df = dataset.to_pandas()
    n_rows, n_cols = df.shape
    cols = list(df.columns)

    # Nomi non snake_case
    non_snake = [c for c in cols if not _is_snake_case(str(c))]

    # Nomi duplicati
    seen: set[str] = set()
    dup: list[str] = []
    for c in cols:
        if c in seen and c not in dup:
            dup.append(c)
        seen.add(c)

    # Colonne vuote
    empty = [c for c in cols if df[c].isna().all()]

    # High null (esclude le completamente vuote per evitare doppia segnalazione)
    high_null: dict[str, float] = {}
    if n_rows > 0:
        for c in cols:
            if c in empty:
                continue
            ratio = float(df[c].isna().sum()) / n_rows
            if ratio > high_null_threshold:
                high_null[c] = ratio

    # Righe duplicate
    dup_rows = int(df.duplicated().sum())

    # Tipi
    dtypes = {c: str(df[c].dtype) for c in cols}

    return ProfileReport(
        n_rows=n_rows,
        n_cols=n_cols,
        non_snake_case_columns=non_snake,
        duplicated_column_names=dup,
        empty_columns=empty,
        high_null_columns=high_null,
        duplicate_rows=dup_rows,
        dtypes=dtypes,
    )