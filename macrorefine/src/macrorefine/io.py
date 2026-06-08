"""Funzioni per il salvataggio dei Dataset.

Il metodo `Dataset.to_csv()` / `Dataset.to_parquet()` resta disponibile
per scritture semplici. Questo modulo offre invece:

    - Auto-detection del formato dall'estensione
    - Creazione automatica delle cartelle mancanti
    - Salvataggio opzionale della history come file JSON sidecar
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from macrorefine.dataset import Dataset

Format = Literal["csv", "parquet", "json"]
_SUPPORTED_FORMATS: tuple[str, ...] = ("csv", "parquet", "json")


def save_dataset(
    dataset: Dataset,
    path: str | Path,
    *,
    format: Format | None = None,
    save_history: bool = False,
    **writer_kwargs: Any,
) -> Path:
    """Salva un Dataset su disco con utility comode integrate.

    Args:
        dataset: il Dataset da salvare.
        path: percorso di destinazione (le cartelle mancanti vengono create).
        format: formato esplicito ("csv", "parquet", "json"). Se None viene
            dedotto dall'estensione del path.
        save_history: se True salva un file sidecar `<basename>.history.json`
            con l'audit trail completo del Dataset.
        **writer_kwargs: argomenti passati al writer pandas sottostante
            (es. `sep=";"` per CSV, `index=False`, ...).

    Returns:
        Il path effettivo del file scritto.

    Raises:
        ValueError: se il formato non è supportato.
    """
    path = Path(path)
    fmt = (format or _infer_format(path)).lower()

    if fmt not in _SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format: {fmt!r}. "
            f"Supported: {_SUPPORTED_FORMATS}"
        )

    # Crea le cartelle mancanti
    path.parent.mkdir(parents=True, exist_ok=True)

    df = dataset.to_pandas()

    if fmt == "csv":
        writer_kwargs.setdefault("index", False)
        df.to_csv(path, **writer_kwargs)
    elif fmt == "parquet":
        df.to_parquet(path, **writer_kwargs)
    elif fmt == "json":
        writer_kwargs.setdefault("orient", "records")
        writer_kwargs.setdefault("indent", 2)
        writer_kwargs.setdefault("force_ascii", False)
        df.to_json(path, **writer_kwargs)

    if save_history:
        _write_history_sidecar(dataset, path)

    return path


# ----- Helpers privati -----

def _infer_format(path: Path) -> str:
    """Deduce il formato dall'estensione del path."""
    ext = path.suffix.lstrip(".").lower()
    if not ext:
        raise ValueError(
            f"Cannot infer format from path without extension: {path}. "
            f"Pass `format=` explicitly."
        )
    return ext


def _write_history_sidecar(dataset: Dataset, data_path: Path) -> Path:
    """Scrive un file <stem>.history.json accanto al file dati."""
    sidecar = data_path.with_suffix(".history.json")
    rows, cols = dataset.shape
    payload = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "data_file": data_path.name,
        "rows": rows,
        "cols": cols,
        "columns": dataset.columns,
        "steps": [
            {
                "name": r.name,
                "params": r.params,
                "metrics": r.metrics,
            }
            for r in dataset.history
        ],
    }
    sidecar.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
    return sidecar