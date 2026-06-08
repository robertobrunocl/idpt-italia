"""scripts/recipes/cubo5_occupati_istat.py — Recipe cubo 5.

Sorgente: ``data/istat_occupati_provincia_2025_v1.csv`` (107 province ISTAT,
media annua 2025, occupati totali 15-89 anni in migliaia di persone).

Pipeline:
1. Rename colonne CSV ISTAT (REF_AREA, Osservazione) in nomi snake_case.
2. Cast misura numerica (float anglosassone, niente formato italiano).
3. ``LinkProvinceToAGID_byNUTS`` per arricchire con URI AGID + metadata
   (gestisce NUTS-3 standard, NUTS-2 PA via alias, fake-NUTS IT108-IT111).
4. ``EmitQbObservations`` per materializzare il cubo qb come Turtle.

Output: ``output/observations/cubo5_occupati_istat.ttl`` (1 qb:DataSet + 107
qb:Observation = ~1500 triple).

Esecuzione:
    source .venv/bin/activate
    python scripts/recipes/cubo5_occupati_istat.py
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "macrorefine" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "recipes"))

from macrorefine import Dataset, Pipeline, Recipe  # noqa: E402
from macrorefine.steps import CastTypes, RenameColumns  # noqa: E402
from macrorefine.steps.lod import (  # noqa: E402
    EmitQbObservations,
    LinkProvinceToAGID_byNUTS,
)

import idpt_vocab as V  # noqa: E402


PROVINCES_TTL = PROJECT_ROOT / "data" / "provinces.ttl"
NUTS_ALIASES_TTL = PROJECT_ROOT / "output" / "mappings" / "nuts_aliases.ttl"
INPUT_CSV = PROJECT_ROOT / "data" / "istat_occupati_provincia_2025_v1.csv"
OUTPUT_TTL = PROJECT_ROOT / "output" / "observations" / "cubo5_occupati_istat.ttl"


class CuboOccupatiIstatRecipe(Recipe):
    """Recipe per il cubo 5: occupati ISTAT per provincia, media annua 2025."""

    def build(self) -> Pipeline:
        return (
            Pipeline()
            .add(RenameColumns({
                "REF_AREA":     "ref_area",
                "Osservazione": "n_occupati",
            }))
            .add(CastTypes({"n_occupati": "float"}))
            .add(LinkProvinceToAGID_byNUTS(
                nuts_column="ref_area",
                provinces_ttl=PROVINCES_TTL,
                nuts_aliases_ttl=NUTS_ALIASES_TTL,
            ))
            .add(EmitQbObservations(
                dataset_uri=V.CUBE_OCCUPATI_ISTAT,
                dsd_uri=V.DSD_OCCUPATI_ISTAT,
                obs_uri_template=V.IDPT_NS + "obs-occupati-{codice_istat}-2025",
                dimensions={"uri_agid": V.PROVINCIA},
                constant_dimensions={
                    V.ANNO_RIFERIMENTO: '"2025"^^xsd:gYear',
                },
                measures={"n_occupati": V.NUMERO_OCCUPATI},
                dataset_attributes={
                    V.SDMX_ATTR_UNIT_MEASURE: '"migliaia di persone"@it',
                },
                dataset_metadata={
                    "title": "Occupati ISTAT per provincia, media annua 2025",
                    "description": (
                        "Occupati totali (entrambi i sessi, 15-89 anni), media annua "
                        "2025, per le 107 province italiane. Fonte: ISTAT, Rilevazione "
                        "Forze di Lavoro (RFL). Valori in migliaia di persone."
                    ),
                    "issued": "2026-05-29",
                    "source": "https://esplora.istat.it/",
                    "license": V.LICENSE_CC_BY_3_0_IT,
                    "rights": (
                        "Dati derivati da ISTAT (licenza CC-BY 3.0 IT), "
                        "riconfezionati in formato Linked Open Data."
                    ),
                },
                output_path=OUTPUT_TTL,
            ))
        )


def main() -> int:
    if not INPUT_CSV.exists():
        print(f"✗ CSV non trovato: {INPUT_CSV}")
        return 1

    print(f"=== Recipe Cubo 5 — occupati ISTAT ===")
    print(f"Input:  {INPUT_CSV}")
    print(f"Output: {OUTPUT_TTL}")
    print()

    ds = Dataset.from_csv(INPUT_CSV, dtype=str, encoding="utf-8-sig")
    print(f"✓ CSV caricato: {ds.shape[0]} righe")

    result = CuboOccupatiIstatRecipe().apply(ds)

    # Stampa metriche dello step Emit (ultimo della pipeline)
    emit_rec = result.history[-1]
    print()
    print(f"✓ Cubo emesso: {OUTPUT_TTL}")
    print(f"  observations_emitted: {emit_rec.metrics['observations_emitted']}")
    print(f"  triples_written:      {emit_rec.metrics['triples_written']}")
    if emit_rec.metrics.get("rows_skipped_missing_dimension", 0) > 0:
        print(f"  ⚠ righe skipped:    {emit_rec.metrics['rows_skipped_missing_dimension']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
