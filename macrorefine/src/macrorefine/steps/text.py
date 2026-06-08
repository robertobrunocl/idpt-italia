"""Step per la manipolazione e normalizzazione del testo."""
from __future__ import annotations

import re
import unicodedata
from typing import Any

import pandas as pd

from macrorefine.dataset import Dataset
from macrorefine.history import StepRecord
from macrorefine.step import PipelineStep


def normalize_text(value: Any) -> str | None:
    """Normalizza una stringa per il matching tra dataset.

    Operazioni applicate, in ordine:
        1. apostrofi tipografici (’, ‘, `) → apostrofo ASCII (')
        2. rimozione degli accenti (NFKD + drop dei diacritici)
        3. lowercase
        4. collasso degli spazi multipli + strip

    Ritorna None per valori None/NaN.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value)
    text = text.replace("\u2019", "'").replace("\u2018", "'").replace("`", "'")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


class AddNormalizedKey(PipelineStep):
    """Aggiunge una colonna ausiliaria con il testo della source normalizzato.

    Utile per preparare colonne-chiave per i join tra dataset eterogenei
    (lowercase, no accenti, no apostrofi tipografici, spazi normalizzati).

    Args:
        source: nome della colonna sorgente.
        target: nome della nuova colonna con il testo normalizzato.
    """

    def __init__(self, source: str, target: str) -> None:
        super().__init__()
        self.source = source
        self.target = target

    def apply(self, dataset: Dataset) -> Dataset:
        df = dataset.to_pandas()
        if self.source not in df.columns:
            raise KeyError(f"Column not found: {self.source!r}")
        df[self.target] = df[self.source].apply(normalize_text)
        record = StepRecord(
            name=self.name,
            params={"source": self.source, "target": self.target},
        )
        return dataset.with_data(df, step_record=record)