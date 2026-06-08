"""ProjectGDPRegimeComposition — Plan B per la dim. 3 IDPT sul comparto pubblico.

L'INPS non pubblica la composizione regime delle pensioni della Gestione
Dipendenti Pubblici (GDP) a granularità provincia × regime. Il cubo OLAP
"regime di liquidazione" esclude i pubblici per costruzione (vedi sez. 6 di
PROGETTO_CONTESTO.md). Strategia adottata al check-point ontologico (sez. 10.14,
"Plan B"):

1. Dal CSV nazionale ``inps_pensioni_decorrenza_pubblici_tutte_categorie_2026_v1.csv``
   (46 righe: 1 "Decorrenza anteriore al 31/12/1980" + 45 anni 1981-2025)
   calcoliamo la **composizione regime nazionale** applicando l'euristica
   decorrenza→regime documentata in sez. 10.6:

   - decorrenza ≤ 1995  → regime "Retributivo"
   - 1996 ≤ dec ≤ 2011  → regime "Misto Riforma Dini"
   - 2012 ≤ dec ≤ 2025  → regime "Misto Riforma Fornero"
   - "Contributivo Puro" → 0 nel periodo coperto dal CSV (raro per vecchiaia GDP)

2. **Proiezione provinciale**: per ogni provincia conosciamo il numero pensioni
   GDP totale dal cubo 1 (gestione=Pubblici). Moltiplichiamo per le % regime
   nazionali → stima numero pensioni GDP per provincia × regime.

3. Le osservazioni risultanti saranno marcate come ``obsStatus=E`` +
   ``prov:wasDerivedFrom`` (origini: obs cubo 1 + obs cubo 4) nel cubo 9
   ``idpt:cubo-plan-b-gdp-projected``. Questo step lavora a livello tabellare;
   la semantica RDF la applichiamo nella Recipe.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from macrorefine.history import StepRecord
from macrorefine.step import PipelineStep

if TYPE_CHECKING:
    from macrorefine.dataset import Dataset


# Soglie default — sez. 10.6 di PROGETTO_CONTESTO.md.
# Chiave = regime di liquidazione (corrisponde alla code-list SKOS
# idpt:regimi-liquidazione). Valore = (anno_min, anno_max) inclusivi.
# L'anno "Decorrenza anteriore al 31/12/1980" è gestito specialmente come 1980
# (≤ 1995 → retributivo).
DEFAULT_THRESHOLDS: dict[str, tuple[int, int]] = {
    "retributivo":         (1900, 1995),
    "misto-dini":          (1996, 2011),
    "misto-fornero":       (2012, 2025),
    "contributivo-puro":   (9999, 9999),   # mai nel periodo CSV; placeholder
}


def _parse_decorrenza_year(label: str) -> int | None:
    """Estrae l'anno da una riga del CSV decorrenza GDP.

    - "1981", "1982", ..., "2025" → int
    - "Decorrenza anteriore al 31/12/1980" → 1980 (rappresentativo del bucket)
    - "Totale" o altro → None
    """
    s = str(label).strip()
    if s == "Totale":
        return None
    # Cerca un anno 19xx/20xx
    import re
    m = re.search(r"(19|20)\d{2}", s)
    if m:
        return int(m.group(0))
    return None


def _parse_italian_number(s: str) -> float | None:
    """Parse formato italiano '9.999,99' → float, '-' → None."""
    s = s.strip()
    if not s or s == "-":
        return None
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _load_decorrenza_csv(
    csv_path: Path, data_start_line: int = 35
) -> pd.DataFrame:
    """Carica il CSV decorrenza GDP, restituendo un df con colonne pulite.

    Headers attese: "Anno di decorrenza", "Numero Pensioni",
    "Età media alla decorrenza", "Importo medio mensile", ecc.

    Output df con colonne (tutte numeric/int):
    - ``anno_decorrenza_label``: stringa originale (es. "1990", "Decorrenza anteriore al 31/12/1980")
    - ``anno_decorrenza`` (int): 1980 per "anteriore", altrimenti l'anno parsato
    - ``is_pre_1981`` (bool): True solo per la riga "Decorrenza anteriore al 31/12/1980"
    - ``numero_pensioni`` (int)
    - ``eta_media_decorrenza`` (float, anni)
    - ``importo_medio_mensile`` (float, euro)
    """
    import re
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i < data_start_line:
                continue
            cells = re.findall(r'"([^"]*)"', line)
            if len(cells) < 3:
                continue
            label = cells[0].strip()
            if label == "Totale" or not label:
                continue
            year = _parse_decorrenza_year(label)
            if year is None:
                continue
            num_pens = _parse_italian_number(cells[2])
            # cells[3] (età decorrenza) e cells[4] (importo medio mensile)
            # opzionali: CSV reale INPS ne ha 7, CSV fittizi nei test ne hanno 3.
            eta_decorr = _parse_italian_number(cells[3]) if len(cells) > 3 else None
            imp_mensile = _parse_italian_number(cells[4]) if len(cells) > 4 else None
            if num_pens is None:
                continue
            rows.append({
                "anno_decorrenza_label":  label,
                "anno_decorrenza":        year,
                "is_pre_1981":            "anteriore" in label.lower(),
                "numero_pensioni":        int(num_pens),
                "eta_media_decorrenza":   eta_decorr,
                "importo_medio_mensile":  imp_mensile,
            })
    return pd.DataFrame(rows)


def compute_national_regime_composition(
    decorrenza_df: pd.DataFrame,
    thresholds: dict[str, tuple[int, int]] | None = None,
) -> dict[str, float]:
    """Calcola la composizione regime nazionale GDP da dati decorrenza.

    Args:
        decorrenza_df: df con colonne ``anno_decorrenza`` (int) e
            ``numero_pensioni`` (int).
        thresholds: vedi DEFAULT_THRESHOLDS. Default applica l'euristica
            decorrenza→regime di sez. 10.6.

    Returns:
        dict {regime_notation: fraction}, con somma frazioni = 1.0 (sui regimi
        coperti dal CSV).
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    totals: dict[str, int] = {regime: 0 for regime in thresholds}
    for _, row in decorrenza_df.iterrows():
        year = int(row["anno_decorrenza"])
        n = int(row["numero_pensioni"])
        for regime, (year_min, year_max) in thresholds.items():
            if year_min <= year <= year_max:
                totals[regime] += n
                break  # ogni anno appartiene a 1 solo bucket

    total_all = sum(totals.values())
    if total_all == 0:
        return {regime: 0.0 for regime in thresholds}
    return {regime: totals[regime] / total_all for regime in thresholds}


class ProjectGDPRegimeComposition(PipelineStep):
    """Applica il Plan B GDP: proietta la composizione regime nazionale sulle 107 province.

    Args:
        count_column: nome colonna con il conteggio pensioni Pubblici per provincia
            (input dal cubo 1, dimensione gestione = Pubblici).
        decorrenza_csv: path al CSV INPS decorrenza GDP tutte categorie (cubo 4).
        output_shape: "long" (espande in 4 righe per provincia × 4 regimi) o
            "wide" (4 colonne aggiunte al df). Default "long" (coerente con
            cubo 9 che ha 428 obs = 107 × 4).
        thresholds: override delle soglie decorrenza→regime. Default
            DEFAULT_THRESHOLDS (sez. 10.6).
        keep_extra_columns: se True, le colonne non-numeriche del df di input
            vengono replicate nelle 4 righe espanse (utile per preservare
            URI provincia AGID, anno snapshot, ecc.). Default True.

    Output:
        - shape="long": df con 4 × len(input) righe, nuove colonne
          ``regime_notation`` e ``numero_pensioni_proiettato`` + colonna
          ``_status="estimated_plan_b"``.
        - shape="wide": df con stesse righe di input, 4 nuove colonne
          ``numero_pensioni_proiettato_{regime}``.
    """

    SUPPORTED_SHAPES = ("long", "wide")

    def __init__(
        self,
        count_column: str,
        decorrenza_csv: str | Path,
        output_shape: str = "long",
        thresholds: dict[str, tuple[int, int]] | None = None,
        keep_extra_columns: bool = True,
    ) -> None:
        super().__init__()
        if output_shape not in self.SUPPORTED_SHAPES:
            raise ValueError(
                f"output_shape='{output_shape}' non supportato. "
                f"Disponibili: {self.SUPPORTED_SHAPES}"
            )
        self.count_column = count_column
        self.decorrenza_csv = Path(decorrenza_csv)
        self.output_shape = output_shape
        self.thresholds = thresholds if thresholds is not None else dict(DEFAULT_THRESHOLDS)
        self.keep_extra_columns = keep_extra_columns
        # Cache lazy
        self._composition: dict[str, float] | None = None
        self._national_total: int | None = None

    def _load_composition(self) -> None:
        if not self.decorrenza_csv.exists():
            raise FileNotFoundError(
                f"ProjectGDPRegimeComposition: CSV decorrenza non trovato: "
                f"{self.decorrenza_csv}"
            )
        decorrenza_df = _load_decorrenza_csv(self.decorrenza_csv)
        self._composition = compute_national_regime_composition(
            decorrenza_df, self.thresholds
        )
        self._national_total = int(decorrenza_df["numero_pensioni"].sum())

    def apply(self, dataset: "Dataset") -> "Dataset":
        df = dataset.to_pandas()
        if self.count_column not in df.columns:
            raise KeyError(
                f"ProjectGDPRegimeComposition: colonna conteggio "
                f"'{self.count_column}' non presente. "
                f"Disponibili: {list(df.columns)}"
            )

        if self._composition is None:
            self._load_composition()

        regimes = list(self._composition.keys())  # type: ignore[union-attr]

        if self.output_shape == "long":
            # Espandi 1 riga in 4: una per regime
            rows = []
            for _, src in df.iterrows():
                count = src[self.count_column]
                for regime in regimes:
                    fraction = self._composition[regime]  # type: ignore[index]
                    new_row = src.to_dict() if self.keep_extra_columns else {}
                    new_row["regime_notation"] = regime
                    new_row["numero_pensioni_proiettato"] = (
                        float(count) * fraction if pd.notna(count) else float("nan")
                    )
                    new_row["_status"] = "estimated_plan_b"
                    rows.append(new_row)
            result = pd.DataFrame(rows)
        else:
            # Wide: 4 nuove colonne
            result = df.copy()
            for regime in regimes:
                col = f"numero_pensioni_proiettato_{regime}"
                fraction = self._composition[regime]  # type: ignore[index]
                result[col] = result[self.count_column].astype(float) * fraction
            result["_status"] = "estimated_plan_b"

        record = StepRecord(
            name=self.name,
            params={
                "count_column": self.count_column,
                "decorrenza_csv": str(self.decorrenza_csv),
                "output_shape": self.output_shape,
                "thresholds": {k: list(v) for k, v in self.thresholds.items()},
                "keep_extra_columns": self.keep_extra_columns,
            },
            metrics={
                "input_rows": int(len(df)),
                "output_rows": int(len(result)),
                "national_total_gdp": self._national_total,
                "composition_percentages": {
                    k: round(v * 100, 2)
                    for k, v in (self._composition or {}).items()
                },
                "regimes_used": regimes,
            },
        )
        return dataset.with_data(result, step_record=record)
