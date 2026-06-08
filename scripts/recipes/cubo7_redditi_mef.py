"""scripts/recipes/cubo7_redditi_mef.py — Recipe cubo 7.

Sorgente: ``data/mef_redditi_irpef_comune_2024_v1.csv`` (7897 comuni italiani,
anno di imposta 2024, redditi prodotti nel 2023). 53 colonne wide.

Pipeline:
1. Lettura CSV con ``keep_default_na=False`` per evitare NA-bug Napoli
   (92 comuni con Sigla="NA" → NaN in pandas default).
2. ``AggregateMEFRedditiByProvincia``: drop riga sentinella Sigla="0", cast
   delle 10 colonne reddito (5 voci × 2 misure), group-by Sigla + unpivot
   wide→long → 535 righe (107 sigle × 5 voci).
3. ``LinkProvinceToAGID_bySigla`` per arricchire con URI AGID + codice ISTAT.
4. ``EmitQbObservations`` per materializzare ``output/observations/cubo7_redditi_mef.ttl``.

Output: 535 obs, ognuna con dimensioni (provincia × anno × voceReddito) +
2 misure (frequenzaDichiaranti + ammontareTotale).

Esecuzione:
    source .venv/bin/activate
    python scripts/recipes/cubo7_redditi_mef.py
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "macrorefine" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "recipes"))

from macrorefine import Dataset, Pipeline, Recipe  # noqa: E402
from macrorefine.steps.lod import (  # noqa: E402
    AggregateMEFRedditiByProvincia,
    EmitQbObservations,
    LinkProvinceToAGID_bySigla,
)

import idpt_vocab as V  # noqa: E402


PROVINCES_TTL = PROJECT_ROOT / "data" / "provinces.ttl"
INPUT_CSV = PROJECT_ROOT / "data" / "mef_redditi_irpef_comune_2024_v1.csv"
OUTPUT_TTL = PROJECT_ROOT / "output" / "observations" / "cubo7_redditi_mef.ttl"

# Mapping voci MEF → URI SKOS Concept (5 voci, dichiarate in code_lists.ttl)
VOCI_URI = {
    "v2": V.IDPT_NS + "voce-redd-lavoro-dipendente",
    "v4": V.IDPT_NS + "voce-redd-lavoro-autonomo",
    "v5": V.IDPT_NS + "voce-redd-imprenditore-ord",
    "v6": V.IDPT_NS + "voce-redd-imprenditore-sempl",
    "v7": V.IDPT_NS + "voce-redd-partecipazione",
}


class CuboRedditiMefRecipe(Recipe):
    """Recipe per il cubo 7: redditi MEF per provincia × voce, anno 2024."""

    def build(self) -> Pipeline:
        return (
            Pipeline()
            .add(AggregateMEFRedditiByProvincia(
                voci_uri=VOCI_URI,
                sigla_column="Sigla Provincia",
                sentinel_sigla="0",
            ))
            .add(LinkProvinceToAGID_bySigla(
                sigla_column="Sigla Provincia",
                provinces_ttl=PROVINCES_TTL,
            ))
            .add(EmitQbObservations(
                dataset_uri=V.CUBE_REDDITI_MEF,
                dsd_uri=V.DSD_REDDITI_MEF,
                obs_uri_template=V.IDPT_NS + "obs-redditi-{codice_istat}-{voce_short}-2024",
                dimensions={
                    "uri_agid":  V.PROVINCIA,
                    "voce_uri":  V.VOCE_REDDITO,
                },
                constant_dimensions={
                    V.ANNO_RIFERIMENTO: '"2024"^^xsd:gYear',
                },
                measures={
                    "frequenza_dichiaranti": V.FREQUENZA_DICHIARANTI,
                    "ammontare_totale":      V.AMMONTARE_TOTALE,
                },
                dataset_metadata={
                    "title": "Redditi IRPEF per provincia × voce di reddito, anno 2024",
                    "description": (
                        "Dichiarazioni IRPEF aggregate da livello comunale (7897 comuni) a "
                        "livello provinciale (107 province AGID) via group-by su Sigla "
                        "Provincia. 5 voci di reddito da lavoro (v2/v4/v5/v6/v7) selezionate "
                        "come componenti del denominatore della dim. 2 IDPT (peso economico). "
                        "Anno di imposta 2024 (redditi 2023). Fonte: MEF, Dipartimento delle "
                        "Finanze. Importi in euro."
                    ),
                    "issued": "2026-05-29",
                    "source": "https://www1.finanze.gov.it/finanze/analisi_stat/",
                    "license": V.LICENSE_CC_BY_3_0_IT,
                    "rights": (
                        "Dati derivati da MEF Dipartimento delle Finanze (CC-BY 3.0 IT), "
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

    print(f"=== Recipe Cubo 7 — redditi MEF ===")
    print(f"Input:  {INPUT_CSV}")
    print(f"Output: {OUTPUT_TTL}")
    print()

    ds = Dataset.from_csv(
        INPUT_CSV, sep=";", dtype=str, encoding="utf-8",
        keep_default_na=False,  # fix bug NA Napoli
    )
    print(f"✓ CSV caricato: {ds.shape[0]} comuni")

    result = CuboRedditiMefRecipe().apply(ds)

    # Stampa metriche per step (più informativo per il MEF)
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
