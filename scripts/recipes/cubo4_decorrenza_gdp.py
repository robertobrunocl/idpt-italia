"""scripts/recipes/cubo4_decorrenza_gdp.py — Recipe cubo 4.

Sorgente: ``data/inps_pensioni_decorrenza_pubblici_tutte_categorie_2026_v1.csv``
(CSV INPS "anno di decorrenza" nazionale GDP tutte le categorie, 46 righe).

Pipeline:
1. Lettura via ``_load_decorrenza_csv`` helper (csv parsing del template OLAP
   sporco). Output: 46 righe con colonne anno_decorrenza_label, anno_decorrenza
   (int, 1980 per "anteriore al 31/12/1980"), is_pre_1981 (bool),
   numero_pensioni, eta_media_decorrenza, importo_medio_mensile.
2. Aggiunta colonne costanti: area_uri = idpt:area-italia,
   obs_status_uri = sdmx-code:obsStatus-E per pre_1981, sdmx-code:obsStatus-A altrove.
3. ``EmitQbObservations`` stile A con 3 misure + dimensione annoDecorrenza
   tipata xsd:gYear + obs_status_column per gestione mista A/E.

Output: 46 obs in ``output/observations/cubo4_decorrenza_gdp.ttl``.

Esecuzione:
    source .venv/bin/activate
    python scripts/recipes/cubo4_decorrenza_gdp.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "macrorefine" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "recipes"))

from macrorefine import Dataset, Pipeline, Recipe  # noqa: E402
from macrorefine.steps.lod import EmitQbObservations  # noqa: E402
from macrorefine.steps.lod.project import _load_decorrenza_csv  # noqa: E402

import idpt_vocab as V  # noqa: E402


INPUT_CSV = PROJECT_ROOT / "data" / "inps_pensioni_decorrenza_pubblici_tutte_categorie_2026_v1.csv"
OUTPUT_TTL = PROJECT_ROOT / "output" / "observations" / "cubo4_decorrenza_gdp.ttl"


class CuboDecorrenzaGdpRecipe(Recipe):
    """Recipe cubo 4: decorrenza GDP nazionale, 1980-2025."""

    def build(self) -> Pipeline:
        return (
            Pipeline()
            .add(EmitQbObservations(
                dataset_uri=V.CUBE_PENSIONI_DECORRENZA_GDP,
                dsd_uri=V.DSD_PENSIONI_DECORRENZA_GDP,
                obs_uri_template=V.IDPT_NS + "obs-decorrenza-italia-{anno_decorrenza}",
                dimensions={
                    "area_uri":        V.AREA_GEOGRAFICA,
                    "anno_decorrenza": (V.ANNO_DECORRENZA, "xsd:gYear"),
                },
                measures={
                    "numero_pensioni":       V.NUMERO_PENSIONI,
                    "importo_medio_mensile": V.IMPORTO_MEDIO_MENSILE,
                    "eta_media_decorrenza":  V.ETA_MEDIA_DECORRENZA,
                },
                obs_status_column="obs_status_uri",
                dataset_metadata={
                    "title": "Pensioni GDP per anno di decorrenza, Italia, 2026",
                    "description": (
                        "Pensioni della Gestione Dipendenti Pubblici (GDP) vigenti al "
                        "1.1.2026, distribuzione nazionale per anno di decorrenza "
                        "(1981-2025 + 'anteriore al 31/12/1980' aggregato a 1980 con "
                        "obsStatus=E). Tutte le categorie GDP (vecchiaia + anzianità + "
                        "invalidità + superstiti). Totale nazionale: 3.171.265 pensioni. "
                        "Input principale per il Plan B GDP del cubo 9 "
                        "(proiezione composizione regime su province via euristica "
                        "decorrenza→regime, sez. 10.6 di PROGETTO_CONTESTO.md). Fonte: "
                        "INPS Osservatorio Statistico."
                    ),
                    "issued": "2026-05-29",
                    "source": "https://www.inps.it/osservatorio/pensioni-vigenti",
                    "license": V.LICENSE_CC_BY_4_0,
                    "rights": (
                        "Dati derivati da INPS (licenza IODL 2.0), riconfezionati come "
                        "Linked Open Data con licenza CC-BY 4.0 (compatibile)."
                    ),
                },
                output_path=OUTPUT_TTL,
            ))
        )


def main() -> int:
    if not INPUT_CSV.exists():
        print(f"✗ CSV non trovato: {INPUT_CSV}")
        return 1

    print(f"=== Recipe Cubo 4 — decorrenza GDP nazionale ===")
    print(f"Input:  {INPUT_CSV}")
    print(f"Output: {OUTPUT_TTL}")
    print()

    df = _load_decorrenza_csv(INPUT_CSV)
    print(f"✓ CSV caricato: {len(df)} righe (46 attese: 1 'anteriore 1980' + 45 anni 1981-2025)")

    # Aggiungi colonne costanti per Emit
    df["area_uri"] = V.AREA_ITALIA
    df["obs_status_uri"] = df["is_pre_1981"].map(
        lambda b: V.SDMX_CODE_OBS_STATUS_E if b else V.SDMX_CODE_OBS_STATUS_A
    )

    result = CuboDecorrenzaGdpRecipe().apply(Dataset(df))

    print()
    rec = result.history[-1]
    print(f"  EmitQbObservations:")
    for k, v in rec.metrics.items():
        if isinstance(v, (list, dict)) and len(str(v)) > 80:
            print(f"        {k}: {type(v).__name__} ({len(v)} items)")
        else:
            print(f"        {k}: {v}")

    n_pre_1981 = int(df["is_pre_1981"].sum())
    print()
    print(f"✓ Osservazioni con obsStatus=E: {n_pre_1981} (riga 'anteriore 1980')")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
