"""scripts/recipes/cubo1_vigenti_residenza.py — Recipe cubo 1.

Sorgente: ``data/inps_pensioni_vigenti_provincia_2026_v1.csv`` (CSV INPS
"vigenti per residenza" 2026, export OLAP con header sporco righe 0-33).

Pipeline:
1. Lettura CSV con ``skiprows=35`` + nomi colonne manuali (17 colonne: 1
   provincia + 1 blank + 15 misure: 5 gestioni × 3 misure {n, media, annuo}).
2. Drop 7 continenti (Europa, Asia, Africa, America Settentrionale/Centrale/
   Meridionale, Oceania) — destinati al futuro dataset "pensioni-estero".
3. Drop riga "Totale".
4. ``ParseItalianNumbers`` sulle 15 colonne numeriche.
5. ``AggregateSardiniaProvinces`` snapshot 8→5 (Carbonia/Olbia-Tempio/
   Ogliastra/Medio Campidano aggregate alle 5 province AGID attuali, con
   somma su conteggi e media pesata sugli importi).
6. ``UnpivotINPSPensioniVigenti`` wide→long: 107 righe × 5 gestioni = 535 obs.
7. ``LinkProvinceToAGID_byName`` (nomi italiani con anomalie tipografiche).
8. ``EmitQbObservations`` stile A con 3 misure.

Output: 535 obs in ``output/observations/cubo1_vigenti_residenza.ttl``.

Esecuzione:
    source .venv/bin/activate
    python scripts/recipes/cubo1_vigenti_residenza.py
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
    AggregateSardiniaProvinces,
    EmitQbObservations,
    LinkProvinceToAGID_byName,
    ParseItalianNumbers,
    UnpivotINPSPensioniVigenti,
)

import idpt_vocab as V  # noqa: E402


PROVINCES_TTL = PROJECT_ROOT / "data" / "provinces.ttl"
INPUT_CSV = PROJECT_ROOT / "data" / "inps_pensioni_vigenti_provincia_2026_v1.csv"
OUTPUT_TTL = PROJECT_ROOT / "output" / "observations" / "cubo1_vigenti_residenza.ttl"

# Nomi colonne dopo lettura raw (17 colonne)
COLUMN_NAMES = [
    "provincia", "_blank",
    "n_PRIV", "media_PRIV", "annuo_PRIV",
    "n_PUB",  "media_PUB",  "annuo_PUB",
    "n_AUTO", "media_AUTO", "annuo_AUTO",
    "n_ASS",  "media_ASS",  "annuo_ASS",
    "n_TOT",  "media_TOT",  "annuo_TOT",
]
NUMERIC_COLUMNS = [c for c in COLUMN_NAMES if c.startswith(("n_", "media_", "annuo_"))]

# 7 aggregati continentali (esclusi: destinati al dataset separato pensioni-estero)
CONTINENTI = {
    "Europa", "Asia", "Africa",
    "America Settentrionale", "America Centrale", "America Meridionale",
    "Oceania",
}

# Mapping gestione INPS → URI SKOS Concept (5 gestioni)
GESTIONI_URI = {
    "PRIV": V.GESTIONE_PRIVATI,
    "PUB":  V.GESTIONE_PUBBLICI,
    "AUTO": V.GESTIONE_AUTONOMI_PARASUB,
    "ASS":  V.GESTIONE_ASSISTENZIALI,
    "TOT":  V.GESTIONE_TOTALE,
}


def load_inps_csv() -> pd.DataFrame:
    """Carica il CSV INPS via csv.reader stdlib (pandas perde 28 righe per
    bug di parsing sul quoting interno del template OLAP INPS).

    Skip-pa le 35 righe di header sporco e la sub-header "Provincia di
    residenza" (riga 35 nel CSV).

    Returns:
        DataFrame con 17 colonne nominate, 1 riga per entità territoriale
        (118 entry: 110 province "INPS-style" + 7 continenti + 1 Totale).
    """
    with open(INPUT_CSV, encoding="utf-8", newline="") as f:
        for _ in range(35):
            next(f)
        reader = csv.reader(f, delimiter=";", quotechar='"')
        rows = list(reader)

    # Filtra righe con esattamente 17 campi + skip sub-header
    rows_clean = [r for r in rows if len(r) == 17 and r[0].strip().strip('"') != "Provincia di residenza"]
    df = pd.DataFrame(rows_clean, columns=COLUMN_NAMES)
    # Strip whitespace + quote dai nomi provincia
    df["provincia"] = df["provincia"].astype(str).str.strip().str.strip('"')
    # Strip whitespace dalle colonne numeriche (INPS lascia spazi finali)
    for c in NUMERIC_COLUMNS:
        df[c] = df[c].astype(str).str.strip().str.strip('"')
    return df


class CuboVigentiResidenzaRecipe(Recipe):
    """Recipe cubo 1: pensioni INPS vigenti per provincia di residenza, 2026."""

    def build(self) -> Pipeline:
        return (
            Pipeline()
            .add(ParseItalianNumbers(columns=NUMERIC_COLUMNS))
            .add(AggregateSardiniaProvinces(
                province_column="provincia",
                count_columns=[
                    "n_PRIV", "n_PUB", "n_AUTO", "n_ASS", "n_TOT",
                    "annuo_PRIV", "annuo_PUB", "annuo_AUTO", "annuo_ASS", "annuo_TOT",
                ],
                weight_pairs={
                    "media_PRIV": "n_PRIV",
                    "media_PUB":  "n_PUB",
                    "media_AUTO": "n_AUTO",
                    "media_ASS":  "n_ASS",
                    "media_TOT":  "n_TOT",
                },
            ))
            .add(UnpivotINPSPensioniVigenti(
                gestioni=GESTIONI_URI,
                province_column="provincia",
            ))
            .add(LinkProvinceToAGID_byName(
                name_column="provincia",
                provinces_ttl=PROVINCES_TTL,
            ))
            .add(EmitQbObservations(
                dataset_uri=V.CUBE_PENSIONI_VIGENTI_RESIDENZA,
                dsd_uri=V.DSD_PENSIONI_VIGENTI_RESIDENZA,
                obs_uri_template=(
                    V.IDPT_NS + "obs-vigenti-{codice_istat}-2026-{tipo_gestione_short}"
                ),
                dimensions={
                    "uri_agid":          V.PROVINCIA,
                    "tipo_gestione_uri": V.TIPO_GESTIONE,
                },
                constant_dimensions={
                    V.ANNO_RIFERIMENTO: '"2026"^^xsd:gYear',
                },
                measures={
                    "n_pensioni":                V.NUMERO_PENSIONI,
                    "importo_medio_mensile":     V.IMPORTO_MEDIO_MENSILE,
                    "importo_annuo_complessivo": V.IMPORTO_ANNUO_COMPLESSIVO,
                },
                dataset_metadata={
                    "title": "Pensioni INPS vigenti per provincia di residenza, 1.1.2026",
                    "description": (
                        "Numero pensioni e importi per le 107 province italiane, snapshot "
                        "al 1.1.2026, per 5 tipi di gestione (privati, pubblici, autonomi/"
                        "parasub, assistenziali, totale). Aggregazione 8 ex-province sarde "
                        "INPS → 5 province AGID attuali con somma su conteggi e media "
                        "pesata sugli importi. Importo annuo in milioni di euro. Fonte: "
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

    print(f"=== Recipe Cubo 1 — pensioni INPS vigenti residenza ===")
    print(f"Input:  {INPUT_CSV}")
    print(f"Output: {OUTPUT_TTL}")
    print()

    df = load_inps_csv()
    print(f"✓ CSV caricato: {len(df)} righe (entità territoriali + Totale + continenti)")

    # Drop continenti + Totale (prima della Recipe)
    df_clean = df[~df["provincia"].isin(CONTINENTI | {"Totale"})].copy()
    print(f"✓ Drop 7 continenti + Totale: {len(df_clean)} righe province INPS-style")
    if len(df_clean) != 110:
        print(f"⚠ Atteso 110 entry territoriali, trovate {len(df_clean)} — investiga")

    result = CuboVigentiResidenzaRecipe().apply(Dataset(df_clean))

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
