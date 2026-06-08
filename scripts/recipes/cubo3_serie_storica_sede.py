"""scripts/recipes/cubo3_serie_storica_sede.py — Recipe cubo 3.

Sorgente: ``data/inps_pensioni_vigenti_serie_storica_provincia_1998_2026_v1.csv``
(CSV INPS serie storica 1998-2026, 106 sedi × 29 anni × 1 gestione aggregata =
gestione-totale, già filtrata su Privati+Pubblici+Autonomi+Assistenziali nel
cubo OLAP).

Cubo stile B (qb:measureType, 1 obs = 1 misura). Per ogni (sede × anno) emette
3 obs: n_pensioni + importo_medio_mensile (primarie) + importo_annuo_complessivo
(stimata, obsStatus=E + prov:wasDerivedFrom).

Cardinalità attesa: ~9.123 obs (106 × 29 × 3 - 99 obs scartate per
BAT/Fermo/Monza 1998-2008 con celle "-").

NB: tipoGestione mantenuta come dimensione costante = idpt:gestione-totale
(semantica coerente: il CSV è proprio l'aggregato delle 4 gestioni standard,
come da scopeNote di gestione-totale).

NB2: Aggregazione retroattiva Sardegna 2005-2011 (sez. 10.9): le 3 sedi sarde
"compositive" (Sassari, Nuoro, Cagliari-e-Sud-Sardegna) hanno per gli anni
1998-2011 valori "delle sole sedi pre-2012", incompleti rispetto al territorio
attuale. Marcato come obsStatus=E con rdfs:comment specifico.

Pipeline:
1. Lettura CSV via csv.reader.
2. Drop riga Totale.
3. ParseItalianNumbers sulle 58 colonne (29 anni × 2 misure).
4. UnpivotINPSSerieStorica wide→long (87 righe max per sede).
5. LinkSedeINPS (NON emette sidecar — già fatto dal cubo 2).
6. Post-processing: obs_status_uri (A normalmente, E per ann+Sardegna 1998-2011)
   + prov_derived_uris.
7. EmitQbObservations stile B.

Esecuzione:
    source .venv/bin/activate
    python scripts/recipes/cubo3_serie_storica_sede.py
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
from macrorefine.steps.lod import (  # noqa: E402
    EmitQbObservations,
    LinkSedeINPS,
    ParseItalianNumbers,
    UnpivotINPSSerieStorica,
)
from macrorefine.steps.lod.link import _slugify_inps  # noqa: E402

import idpt_vocab as V  # noqa: E402


PROVINCES_TTL = PROJECT_ROOT / "data" / "provinces.ttl"
INPUT_CSV = PROJECT_ROOT / "data" / "inps_pensioni_vigenti_serie_storica_provincia_1998_2026_v1.csv"
OUTPUT_TTL = PROJECT_ROOT / "output" / "observations" / "cubo3_serie_storica_sede.ttl"

YEARS = list(range(1998, 2027))  # 29 anni 1998..2026

# 58 colonne misure + 2 (sede + blank) = 60 colonne totali
def _build_column_names() -> list[str]:
    cols = ["sede", "_blank"]
    for year in YEARS:
        cols.extend([f"n_{year}", f"media_{year}"])
    return cols

COLUMN_NAMES = _build_column_names()
NUMERIC_COLUMNS = [c for c in COLUMN_NAMES if c.startswith(("n_", "media_"))]

MEASURE_URIS = {
    "n":   V.NUMERO_PENSIONI,
    "med": V.IMPORTO_MEDIO_MENSILE,
    "ann": V.IMPORTO_ANNUO_COMPLESSIVO,
}

# Sedi sarde "compositive" che dal 2012 in poi hanno assorbito ex-province
SARDINIAN_COMPOSITE_SEDI_SLUGS = {
    "sassari",                       # ha assorbito Olbia-Tempio
    "nuoro",                         # ha assorbito Ogliastra
    "cagliari-e-sud-sardegna",       # ha assorbito Carbonia-Iglesias + Medio Campidano
}


def load_inps_serie_csv() -> pd.DataFrame:
    """Carica via csv.reader skip-pando le 36 righe di header."""
    with open(INPUT_CSV, encoding="utf-8", newline="") as f:
        for _ in range(36):
            next(f)
        reader = csv.reader(f, delimiter=";", quotechar='"')
        rows = list(reader)
    rows_clean = [r for r in rows if len(r) == 60 and r[0].strip().strip('"') != "Totale"]
    df = pd.DataFrame(rows_clean, columns=COLUMN_NAMES)
    df["sede"] = df["sede"].astype(str).str.strip().str.strip('"')
    for c in NUMERIC_COLUMNS:
        df[c] = df[c].astype(str).str.strip().str.strip('"')
    return df


def _compute_obs_status(row: pd.Series) -> str:
    """obsStatus per ogni obs.
    - E per misure stimate (ann) sempre
    - E per le obs delle 3 sedi sarde compositive negli anni 1998-2011
      (territorio incompleto rispetto al perimetro attuale)
    - A altrimenti
    """
    if row["is_estimated"]:
        return V.SDMX_CODE_OBS_STATUS_E
    sede_slug = _slugify_inps(row["sede"])
    if sede_slug in SARDINIAN_COMPOSITE_SEDI_SLUGS and 1998 <= int(row["anno"]) <= 2011:
        return V.SDMX_CODE_OBS_STATUS_E
    return V.SDMX_CODE_OBS_STATUS_A


def _build_prov_derived(row: pd.Series) -> list[str]:
    """prov:wasDerivedFrom per le obs estimate.

    Per la misura `ann` (importo annuo complessivo ricostruito): punta alle
    2 obs primarie n + med della stessa coppia (sede, anno).

    Per le obs delle sedi sarde 1998-2011 (compositive): nessuna obs sorgente
    derivata da altre obs nel grafo (la stima è "implicita" perché il valore
    non viene ricostruito ma solo marcato). Lasciamo lista vuota.
    """
    if not row["is_estimated"]:
        return []
    sede_slug = _slugify_inps(row["sede"])
    return [
        V.IDPT_NS + f"obs-storica-{sede_slug}-{row['anno']}-n",
        V.IDPT_NS + f"obs-storica-{sede_slug}-{row['anno']}-med",
    ]


def main() -> int:
    if not INPUT_CSV.exists():
        print(f"✗ CSV non trovato: {INPUT_CSV}")
        return 1

    print(f"=== Recipe Cubo 3 — serie storica per sede INPS ===")
    print(f"Input:  {INPUT_CSV}")
    print(f"Output: {OUTPUT_TTL}")
    print()

    df = load_inps_serie_csv()
    print(f"✓ CSV caricato: {len(df)} sedi (atteso 106)")

    # Pipeline (Unpivot → LinkSedeINPS per slug sede)
    pipe = (
        Pipeline()
        .add(ParseItalianNumbers(columns=NUMERIC_COLUMNS))
        .add(UnpivotINPSSerieStorica(
            sede_column="sede",
            years=YEARS,
            measure_uris=MEASURE_URIS,
        ))
        .add(LinkSedeINPS(
            sede_column="sede",
            provinces_ttl=PROVINCES_TTL,
            # NON emetti sidecar — già emesso dal cubo 2
            emit_sidecar_to=None,
        ))
    )
    ds_int = pipe.run(Dataset(df))
    df_long = ds_int.to_pandas()
    print(f"✓ Pipeline produce {len(df_long)} righe long")

    # Post-processing: obs_status + prov_derived
    df_long["obs_status_uri"] = df_long.apply(_compute_obs_status, axis=1)
    df_long["prov_derived_uris"] = df_long.apply(_build_prov_derived, axis=1)
    df_long["sede_slug"] = df_long["sede"].apply(_slugify_inps)

    n_status_e = (df_long["obs_status_uri"] == V.SDMX_CODE_OBS_STATUS_E).sum()
    n_estimated = df_long["is_estimated"].sum()
    n_sardinia_retro = n_status_e - n_estimated
    print(f"  Obs status=A primarie: {(df_long['obs_status_uri'] == V.SDMX_CODE_OBS_STATUS_A).sum()}")
    print(f"  Obs status=E stimate (ann):       {n_estimated}")
    print(f"  Obs status=E Sardegna retroattiva: {n_sardinia_retro}")

    # Tipo gestione costante = idpt:gestione-totale
    df_long["tipo_gestione_uri"] = V.GESTIONE_TOTALE

    emit_ds = EmitQbObservations(
        dataset_uri=V.CUBE_PENSIONI_SERIE_STORICA_SEDE,
        dsd_uri=V.DSD_PENSIONI_SERIE_STORICA_SEDE,
        obs_uri_template=(
            V.IDPT_NS + "obs-storica-{sede_slug}-{anno}-{measure_short_slug}"
        ),
        dimensions={
            "uri_sede_inps":     V.SEDE_INPS,
            "tipo_gestione_uri": V.TIPO_GESTIONE,
            "anno":              (V.ANNO_RIFERIMENTO, "xsd:gYear"),
        },
        measures={},  # stile B
        measure_type_column="measure_uri",
        value_column="value",
        obs_status_column="obs_status_uri",
        prov_derived_from_column="prov_derived_uris",
        dataset_metadata={
            "title": "Pensioni INPS — serie storica per sede × anno (1998-2026)",
            "description": (
                "Serie storica 29 anni (1998-2026) delle pensioni vigenti per "
                "106 sedi INPS, gestione = totale aggregato delle 4 gestioni "
                "standard (Privati + Pubblici + Autonomi/Parasub + Assistenziali). "
                "Stile B (qb:measureType, 1 obs = 1 misura). Importo annuo "
                "complessivo ricostruito come n × media × 13 (obsStatus=E + "
                "doppia prov:wasDerivedFrom). Aggregazione retroattiva Sardegna "
                "2005-2011 marcata come obsStatus=E con rdfs:comment per le 3 "
                "sedi compositive (Sassari, Nuoro, Cagliari-e-Sud-Sardegna). "
                "Sedi BAT, Fermo, Monza-Brianza (nate 2009) hanno obs solo "
                "2009-2026 (righe pre-2009 con celle '-' scartate). Fonte: "
                "INPS Osservatorio Statistico."
            ),
            "issued": "2026-05-29",
            "source": "https://www.inps.it/osservatorio/pensioni-vigenti",
            "license": V.LICENSE_CC_BY_4_0,
            "rights": "Dati derivati da INPS (IODL 2.0), riconfezionati LOD con CC-BY 4.0.",
        },
        output_path=OUTPUT_TTL,
    ).apply(ds_int.with_data(df_long, step_name="post-processing"))

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
