"""scripts/recipes/cubo6_indicatori_demografici_istat.py — Recipe cubo 6.

Sorgenti (2 CSV ISTAT):
- ``data/istat_indicatori_demografici_provincia_2026_v1.csv`` (107 × 6 = 642
  righe: POP014, POP1564, POP65OVER, OLDAGEDEPR, AGEINDEX, MEANAGEP @ 2026)
- ``data/istat_natalita_speranza_di_vita_2025_v1.csv`` (107 × 2 = 214 righe:
  BIRTHRATE, LIFEEXP65T @ 2025)

Output: 856 obs in ``output/observations/cubo6_indicatori_demografici_istat.ttl``.

Pipeline:
1. Helper ``read_istat_csv()`` (quoting non standard ISTAT con ``quotechar="'"``)
   carica i 2 CSV; concat in unico df.
2. ``CastTypes`` cast colonna ``Osservazione`` a float.
3. ``EnrichWithStaticMapping`` mappa ``DATA_TYPE`` → ``indicatore_uri`` +
   ``unit_measure_literal``.
4. ``LinkProvinceToAGID_byNUTS`` arricchisce con URI AGID via REF_AREA.
5. ``EmitQbObservations`` emette il TTL con dimensione TIME_PERIOD come
   ``xsd:gYear`` (literal tipato variabile per indicatore: 2026 vs 2025) +
   attributo unitMeasure per obs (% / anni / per mille).

Esecuzione:
    source .venv/bin/activate
    python scripts/recipes/cubo6_indicatori_demografici_istat.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "macrorefine" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "recipes"))

from macrorefine import Dataset, Pipeline, Recipe  # noqa: E402
from macrorefine.steps import CastTypes  # noqa: E402
from macrorefine.steps.lod import (  # noqa: E402
    EmitQbObservations,
    EnrichWithStaticMapping,
    LinkProvinceToAGID_byNUTS,
)

import idpt_vocab as V  # noqa: E402


PROVINCES_TTL = PROJECT_ROOT / "data" / "provinces.ttl"
NUTS_ALIASES_TTL = PROJECT_ROOT / "output" / "mappings" / "nuts_aliases.ttl"
INPUT_CSV_2026 = PROJECT_ROOT / "data" / "istat_indicatori_demografici_provincia_2026_v1.csv"
INPUT_CSV_2025 = PROJECT_ROOT / "data" / "istat_natalita_speranza_di_vita_2025_v1.csv"
OUTPUT_TTL = PROJECT_ROOT / "output" / "observations" / "cubo6_indicatori_demografici_istat.ttl"

# Mapping DATA_TYPE (sigla ISTAT) → URI SKOS Concept (idpt:ind-*)
INDICATORE_TO_URI = {
    "POP014":     V.IDPT_NS + "ind-pop014",
    "POP1564":    V.IDPT_NS + "ind-pop1564",
    "POP65OVER":  V.IDPT_NS + "ind-pop65over",
    "OLDAGEDEPR": V.IDPT_NS + "ind-oldagedepr",
    "AGEINDEX":   V.IDPT_NS + "ind-ageindex",
    "MEANAGEP":   V.IDPT_NS + "ind-meanagep",
    "BIRTHRATE":  V.IDPT_NS + "ind-birthrate",
    "LIFEEXP65T": V.IDPT_NS + "ind-lifeexp65t",
}

# Unità di misura per indicatore (literal stringa, non riportata nel CSV ISTAT)
INDICATORE_TO_UNIT = {
    "POP014":     "%",
    "POP1564":    "%",
    "POP65OVER":  "%",
    "OLDAGEDEPR": "%",
    "AGEINDEX":   "%",
    "MEANAGEP":   "anni",
    "BIRTHRATE":  "per mille",
    "LIFEEXP65T": "anni",
}


def read_istat_csv(path: Path, encoding: str = "utf-8-sig") -> pd.DataFrame:
    """Legge un CSV ISTAT con quoting non standard via csv stdlib.

    Il CSV ISTAT esportato da `esplora.istat.it` usa quotechar `'` (apice
    singolo) anziché `"` standard, e contiene apostrofi italiani non escape-ati
    nei valori (es. ``L'Aquila`` → ``'L"Aquila'`` malformato). Pandas standard
    fallisce o produce shift di colonne; `csv.reader` con `quotechar="'"`
    gestisce correttamente la maggioranza dei casi.
    """
    with open(path, encoding=encoding, newline="") as f:
        reader = csv.reader(f, delimiter=",", quotechar="'", escapechar=None)
        rows = list(reader)
    header, data = rows[0], rows[1:]
    return pd.DataFrame(data, columns=header)


class CuboIndicatoriDemograficiIstatRecipe(Recipe):
    """Recipe cubo 6: indicatori demografici ISTAT (8 indicatori, 2026+2025)."""

    def build(self) -> Pipeline:
        return (
            Pipeline()
            .add(CastTypes({"Osservazione": "float"}))
            .add(EnrichWithStaticMapping(
                source_column="DATA_TYPE",
                mappings={
                    "indicatore_uri":       INDICATORE_TO_URI,
                    "unit_measure_literal": INDICATORE_TO_UNIT,
                },
            ))
            .add(LinkProvinceToAGID_byNUTS(
                nuts_column="REF_AREA",
                provinces_ttl=PROVINCES_TTL,
                nuts_aliases_ttl=NUTS_ALIASES_TTL,
            ))
            .add(EmitQbObservations(
                dataset_uri=V.CUBE_INDICATORI_DEMOGRAFICI_ISTAT,
                dsd_uri=V.DSD_INDICATORI_DEMOGRAFICI_ISTAT,
                obs_uri_template=(
                    V.IDPT_NS + "obs-indicatori-{codice_istat}-{DATA_TYPE}-{TIME_PERIOD}"
                ),
                dimensions={
                    "uri_agid":       V.PROVINCIA,
                    "indicatore_uri": V.INDICATORE_DEMOGRAFICO,
                    # TIME_PERIOD variabile (2026 per 6 indicatori, 2025 per
                    # BIRTHRATE/LIFEEXP65T) → literal tipato xsd:gYear
                    "TIME_PERIOD":    (V.ANNO_RIFERIMENTO, "xsd:gYear"),
                },
                measures={"Osservazione": V.VALORE_INDICATORE},
                observation_attributes={
                    "unit_measure_literal": V.SDMX_ATTR_UNIT_MEASURE,
                },
                dataset_metadata={
                    "title": "Indicatori demografici ISTAT per provincia (2026 + 2025)",
                    "description": (
                        "8 indicatori demografici provinciali (107 entità AGID): 6 al "
                        "1.1.2026 (POP014, POP1564, POP65OVER, OLDAGEDEPR, AGEINDEX, "
                        "MEANAGEP) e 2 al 2025 (BIRTHRATE provvisorio, LIFEEXP65T "
                        "stimato). Unità di misura variabile per indicatore (% / anni "
                        "/ per mille), dichiarata come sdmx-attribute:unitMeasure a "
                        "livello di osservazione. Fonte: ISTAT, esplora.istat.it."
                    ),
                    "issued": "2026-05-29",
                    "source": "https://esplora.istat.it/",
                    "license": V.LICENSE_CC_BY_3_0_IT,
                    "rights": (
                        "Dati derivati da ISTAT (licenza CC-BY 3.0 IT), riconfezionati "
                        "in formato Linked Open Data."
                    ),
                },
                output_path=OUTPUT_TTL,
            ))
        )


def main() -> int:
    print(f"=== Recipe Cubo 6 — indicatori demografici ISTAT ===")
    print(f"Input 1 (2026): {INPUT_CSV_2026}")
    print(f"Input 2 (2025): {INPUT_CSV_2025}")
    print(f"Output: {OUTPUT_TTL}")
    print()

    if not INPUT_CSV_2026.exists() or not INPUT_CSV_2025.exists():
        print("✗ CSV non trovati")
        return 1

    df1 = read_istat_csv(INPUT_CSV_2026)
    df2 = read_istat_csv(INPUT_CSV_2025)
    print(f"✓ CSV 2026 caricato: {df1.shape[0]} righe")
    print(f"✓ CSV 2025 caricato: {df2.shape[0]} righe")

    df = pd.concat([df1, df2], ignore_index=True)
    print(f"✓ Concat: {df.shape[0]} righe totali (atteso 856)")

    result = CuboIndicatoriDemograficiIstatRecipe().apply(Dataset(df))

    print()
    for i, rec in enumerate(result.history, 1):
        print(f"  [{i}] {rec.name}")
        for k, v in rec.metrics.items():
            if isinstance(v, (list, dict)) and len(str(v)) > 80:
                print(f"        {k}: {type(v).__name__} ({len(v)} items)")
            else:
                print(f"        {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
