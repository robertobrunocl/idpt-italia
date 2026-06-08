"""ParseItalianNumbers — parsing del formato numerico italiano.

I CSV INPS adottano il formato italiano "sporco" (visibile nei CSV export
dell'Osservatorio Statistico INPS):

    "394.676 "       → 394676      (separatore migliaia `.`)
    "1.234,56 "      → 1234.56     (separatore decimali `,`)
    "1.000.000,75"   → 1000000.75
    "- "             → NaN         (cella soppressa per privacy)
    ""               → NaN         (cella vuota)

Questo step normalizza le colonne specificate in `float` Python, sostituendo
i valori "sentinella" con NaN. È idempotente: applicato a colonne già numeriche
le lascia inalterate.

Coerente con la decisione metodologica della sez. 4 (riga "Numeri INPS in
formato italiano"): macrorefine ha già `CastTypes` per i casi semplici, ma
il formato italiano richiede pre-processing testuale dedicato.
"""
from __future__ import annotations

import pandas as pd

from macrorefine.column_step import ColumnStep


class ParseItalianNumbers(ColumnStep):
    """Converte stringhe in formato numerico italiano in float64.

    Args:
        columns: nome (o lista) di colonne da convertire.
        na_values: valori stringa da trattare come NaN. Default copre i
            sentinella standard dei CSV INPS: `"-"` (soppressione privacy),
            stringa vuota, `"n.d."`, `"n/a"`.

    Output dtype: `float64` (anche per colonne logicamente intere, perché
    NaN richiede dtype float in pandas pre-2.0; per pandas ≥ 2.0 si può
    successivamente convertire a `Int64` nullable via `CastTypes`).
    """

    def __init__(
        self,
        columns: str | list[str],
        na_values: tuple[str, ...] = ("-", "", "n.d.", "n/a"),
    ) -> None:
        super().__init__(columns)
        self.na_values = tuple(na_values)
        # Normalizziamo la lista degli na_values rimuovendo whitespace
        # (così "- " e "-" sono equivalenti dopo .strip())
        self._na_set: set[str] = {v.strip() for v in self.na_values}

    def transform_column(self, series: pd.Series, column_name: str) -> pd.Series:
        # Idempotenza: se la colonna è già numerica, ritorna senza modifiche.
        if pd.api.types.is_numeric_dtype(series):
            return series

        # Cast a stringa per maneggiare uniformemente NaN, float già castati, ecc.
        # Conserviamo i NaN originali pandas.
        original_na_mask = series.isna()
        s = series.astype(str).str.strip()

        # Maschera dei sentinella → NaN
        sentinel_mask = s.isin(self._na_set)
        na_mask = original_na_mask | sentinel_mask

        # Rimozione separatore migliaia (".") e sostituzione decimale ("," → ".")
        # Importante: prima togliamo i punti, POI sostituiamo la virgola.
        cleaned = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)

        # Conversione a float; valori non parsabili → NaN tramite errors="coerce".
        # `to_numeric` con errors="coerce" è la via canonica pandas.
        parsed = pd.to_numeric(cleaned, errors="coerce")

        # Imponiamo NaN sui sentinella (per coprire eventuali edge case dove
        # "to_numeric" interpretasse "-" come numero negativo malformato).
        parsed = parsed.mask(na_mask)
        return parsed
