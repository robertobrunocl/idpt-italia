"""scripts/recipes/cubo2_regime_sede.py — Recipe cubo 2.

Sorgente: ``data/inps_pensioni_vigenti_regime_liquidazione_provincia_2026_v1.csv``
(CSV INPS "regime di liquidazione" 2026, template OLAP sporco, 106 sedi INPS).

Cubo stile B (``qb:measureType``): 1 obs = 1 misura. Per ogni coppia (sede ×
regime) emette 3 obs: numeroPensioni + importoMedioMensile (primarie) +
importoAnnuoComplessivo (stimata, obsStatus=E + prov:wasDerivedFrom).

Cardinalità: 106 sedi × 1 anno × 4 regimi × 3 measureType = **1.272 obs**.

NB: DSD aggiornata in Fase 5 — la dimensione tipoGestione è stata rimossa
perché il cubo OLAP INPS aggrega già Privati + Autonomi/Parasub (esclude
Pubblici per costruzione). Dichiarato in dcterms:description del DataSet.

Pipeline:
1. Lettura CSV via csv.reader (template OLAP sporco, come cubo 1).
2. Drop riga "Totale" + escludi colonne del 5° regime "Totale" (ridondante).
3. ParseItalianNumbers sulle 8 colonne numeriche (4 regimi × 2 misure).
4. LinkSedeINPS (106 sedi → URI idpt:SedeINPS, emette sidecar inps_to_agid.ttl).
5. UnpivotINPSRegimeSede wide→long stile B: 106 → 1.272 righe.
6. Costruzione colonne obs_status_uri + prov_derived_uris per riga.
7. EmitQbObservations stile B (measure_type_column + value_column).

Output: 1.272 obs in ``output/observations/cubo2_regime_sede.ttl``.

Esecuzione:
    source .venv/bin/activate
    python scripts/recipes/cubo2_regime_sede.py
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "macrorefine" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "recipes"))

from macrorefine import Dataset, Pipeline, Recipe  # noqa: E402
from macrorefine.steps.lod import (  # noqa: E402
    EmitQbObservations,
    LinkSedeINPS,
    ParseItalianNumbers,
    UnpivotINPSRegimeSede,
)
from macrorefine.steps.lod.link import _slugify_inps  # noqa: E402

import idpt_vocab as V  # noqa: E402


PROVINCES_TTL = PROJECT_ROOT / "data" / "provinces.ttl"
INPUT_CSV = PROJECT_ROOT / "data" / "inps_pensioni_vigenti_regime_liquidazione_provincia_2026_v1.csv"
OUTPUT_TTL = PROJECT_ROOT / "output" / "observations" / "cubo2_regime_sede.ttl"
SIDECAR_INPS = PROJECT_ROOT / "output" / "mappings" / "inps_to_agid.ttl"

# 8 colonne numeriche del CSV (escludendo Totale = cols 10-11)
COLUMN_NAMES = [
    "sede", "_blank",
    "n_RETR",    "media_RETR",
    "n_DINI",    "media_DINI",
    "n_FORNERO", "media_FORNERO",
    "n_CONTR",   "media_CONTR",
    "n_TOT",     "media_TOT",  # escluse dall'unpivot
]
NUMERIC_COLUMNS = [c for c in COLUMN_NAMES if c.startswith(("n_", "media_"))]

# Mapping regime_short_in_df → (URI SKOS, slug per URI obs)
REGIMI = {
    "RETR":    (V.REGIME_RETRIBUTIVO,        "retr"),
    "DINI":    (V.REGIME_MISTO_DINI,         "mix-dini"),
    "FORNERO": (V.REGIME_MISTO_FORNERO,      "mix-fornero"),
    "CONTR":   (V.REGIME_CONTRIBUTIVO_PURO,  "contr"),
}

# Mapping measure_short → URI measure-property
MEASURE_URIS = {
    "n":   V.NUMERO_PENSIONI,
    "med": V.IMPORTO_MEDIO_MENSILE,
    "ann": V.IMPORTO_ANNUO_COMPLESSIVO,
}


def load_inps_regime_csv() -> pd.DataFrame:
    """Carica via csv.reader skip-pando le 36 righe di header sporco."""
    with open(INPUT_CSV, encoding="utf-8", newline="") as f:
        for _ in range(36):  # L0-L35
            next(f)
        reader = csv.reader(f, delimiter=";", quotechar='"')
        rows = list(reader)
    rows_clean = [r for r in rows if len(r) == 12 and r[0].strip().strip('"') != "Totale"]
    df = pd.DataFrame(rows_clean, columns=COLUMN_NAMES)
    df["sede"] = df["sede"].astype(str).str.strip().str.strip('"')
    for c in NUMERIC_COLUMNS:
        df[c] = df[c].astype(str).str.strip().str.strip('"')
    return df


def _build_obs_uri(row: pd.Series) -> str:
    """URI obs: idpt:obs-regime-{sede_slug}-2026-{regime}-{measure}."""
    sede_slug = _slugify_inps(row["sede"])
    return (
        V.IDPT_NS + f"obs-regime-{sede_slug}-2026-"
        f"{row['regime_short_slug']}-{row['measure_short_slug']}"
    )


def _build_prov_derived(row: pd.Series) -> list[str]:
    """prov:wasDerivedFrom per la misura stimata (ann) = lista delle 2 obs
    primarie sorgenti (n + med) della stessa sede × regime."""
    if not row["is_estimated"]:
        return []
    sede_slug = _slugify_inps(row["sede"])
    return [
        V.IDPT_NS + f"obs-regime-{sede_slug}-2026-{row['regime_short_slug']}-n",
        V.IDPT_NS + f"obs-regime-{sede_slug}-2026-{row['regime_short_slug']}-med",
    ]


def main() -> int:
    if not INPUT_CSV.exists():
        print(f"✗ CSV non trovato: {INPUT_CSV}")
        return 1

    print(f"=== Recipe Cubo 2 — regime sede ===")
    print(f"Input:        {INPUT_CSV}")
    print(f"Output cubo:  {OUTPUT_TTL}")
    print(f"Sidecar INPS: {SIDECAR_INPS}")
    print()

    df = load_inps_regime_csv()
    print(f"✓ CSV caricato: {len(df)} sedi INPS (atteso 106)")

    # Pipeline: Unpivot DEVE precedere LinkSedeINPS (unpivot rifa il df da
    # zero, perde colonne aggiunte). LinkSedeINPS dedup per slug nel sidecar.
    pipe = (
        Pipeline()
        .add(ParseItalianNumbers(columns=NUMERIC_COLUMNS))
        .add(UnpivotINPSRegimeSede(
            sede_column="sede",
            regimi=REGIMI,
            measure_uris=MEASURE_URIS,
        ))
        .add(LinkSedeINPS(
            sede_column="sede",
            provinces_ttl=PROVINCES_TTL,
            emit_sidecar_to=SIDECAR_INPS,
        ))
    )
    ds_intermediate = pipe.run(Dataset(df))
    df_long = ds_intermediate.to_pandas()
    print(f"✓ Unpivot: {len(df_long)} righe long (atteso 106 × 4 × 3 = 1.272)")

    # Post-processing: obs_status_uri + prov_derived_uris + obs_uri (per template)
    df_long["obs_status_uri"] = df_long["is_estimated"].map(
        lambda b: V.SDMX_CODE_OBS_STATUS_E if b else V.SDMX_CODE_OBS_STATUS_A
    )
    df_long["prov_derived_uris"] = df_long.apply(_build_prov_derived, axis=1)

    # Estraggo slug sede per template URI obs
    df_long["sede_slug"] = df_long["sede"].apply(_slugify_inps)

    print(f"  obs primarie (A): {(~df_long['is_estimated']).sum()}")
    print(f"  obs stimate (E):  {df_long['is_estimated'].sum()}")

    # Emit
    emit_ds = EmitQbObservations(
        dataset_uri=V.CUBE_PENSIONI_REGIME_SEDE,
        dsd_uri=V.DSD_PENSIONI_REGIME_SEDE,
        obs_uri_template=(
            V.IDPT_NS + "obs-regime-{sede_slug}-2026-{regime_short_slug}-{measure_short_slug}"
        ),
        dimensions={
            "uri_sede_inps": V.SEDE_INPS,
            "regime_uri":    V.REGIME_LIQUIDAZIONE,
        },
        constant_dimensions={
            V.ANNO_RIFERIMENTO: '"2026"^^xsd:gYear',
        },
        measures={},  # stile B: ignorato, usa measure_type_column
        measure_type_column="measure_uri",
        value_column="value",
        obs_status_column="obs_status_uri",
        prov_derived_from_column="prov_derived_uris",
        dataset_metadata={
            "title": "Pensioni INPS per sede × regime di liquidazione, 2026",
            "description": (
                "Pensioni vigenti al 1.1.2026 per 106 sedi INPS × 4 regimi di "
                "liquidazione (retributivo, misto-Dini, misto-Fornero, contributivo-"
                "puro), in formato stile B (qb:measureType, 1 obs = 1 misura). "
                "Aggrega Privati + Autonomi/Parasub per costruzione del cubo OLAP "
                "INPS — ESCLUDE Pubblici (la dimensione tipoGestione è rimossa "
                "dalla DSD per onestà). Importo annuo complessivo ricostruito come "
                "numero × media × 13 (obsStatus=E + prov:wasDerivedFrom verso le "
                "2 obs primarie della stessa coppia sede×regime). Asse territoriale "
                "= sede INPS (idpt:SedeINPS), distinta dalla provincia AGID di "
                "residenza del cubo 1. Sidecar inps_to_agid.ttl emesso "
                "contestualmente per la riconciliazione semantica sede ↔ provincia."
            ),
            "issued": "2026-05-29",
            "source": "https://www.inps.it/osservatorio/pensioni-vigenti",
            "license": V.LICENSE_CC_BY_4_0,
            "rights": (
                "Dati derivati da INPS (IODL 2.0), riconfezionati LOD con CC-BY 4.0."
            ),
        },
        output_path=OUTPUT_TTL,
    ).apply(ds_intermediate.with_data(df_long, step_name="post-processing"))

    print()
    rec = emit_ds.history[-1]
    print(f"  EmitQbObservations:")
    for k, v in rec.metrics.items():
        if isinstance(v, (list, dict)) and len(str(v)) > 80:
            print(f"        {k}: {type(v).__name__} ({len(v)} items)")
        else:
            print(f"        {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
