"""scripts/recipes/cubo9_plan_b_gdp_projected.py — Recipe cubo 9.

Cubo derivato (Plan B GDP, sez. 10.14 di PROGETTO_CONTESTO.md): proietta la
composizione regime nazionale GDP (stimata dal cubo 4 via euristica
decorrenza→regime) sulle quote provinciali GDP (dal cubo 1, tipoGestione =
Pubblici).

Tutte le 428 obs emesse hanno:
- ``sdmx-attribute:obsStatus sdmx-code:obsStatus-E`` (Estimated)
- doppia ``prov:wasDerivedFrom``: 1 verso obs cubo 1 della provincia × Pubblici,
  1 verso il qb:DataSet cubo 4 (composizione nazionale)

Cardinalità: 107 province × 1 anno (2026) × 4 regimi = 428 obs.

Pipeline:
1. Helper ``_load_pubblici_per_provincia(cubo1_ttl)`` legge il cubo 1 via SPARQL,
   restituisce df 107 righe con (uri_agid, codice_istat, n_pubblici, obs_uri_cubo1).
2. ``ProjectGDPRegimeComposition(shape="long")`` espande 107 → 428 righe con
   colonne (regime_notation, numero_pensioni_proiettato, _status).
3. Post-processing: aggiunge ``regime_uri``, ``regime_short``,
   ``prov_derived_uris`` (lista 2 URI per riga), ``obs_status_uri`` (uniforme E).
4. ``EmitQbObservations`` con ``obs_status_column`` + ``prov_derived_from_column``.

Esecuzione:
    source .venv/bin/activate
    python scripts/recipes/cubo9_plan_b_gdp_projected.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "macrorefine" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "recipes"))

from macrorefine import Dataset, Pipeline, Recipe  # noqa: E402
from macrorefine.steps.lod import (  # noqa: E402
    EmitQbObservations,
    ProjectGDPRegimeComposition,
)

import idpt_vocab as V  # noqa: E402

def _q(template: str) -> str:
    # Sostituisce il namespace idpt placeholder con quello attuale di V.IDPT_NS.
    # Permette di tenere i template SPARQL leggibili (con namespace placeholder
    # `https://example.org/idpt/`) ma di eseguirli correttamente anche dopo che
    # `scripts/finalize_namespace.py` ha aggiornato V.IDPT_NS al deploy GitHub
    # Pages. Senza questa funzione le query non troverebbero nulla nei TTL
    # emessi dopo il rename del namespace.
    return template.replace(
        "PREFIX idpt: <https://example.org/idpt/>",
        f"PREFIX idpt: <{V.IDPT_NS}>",
    )



DECORRENZA_CSV = (
    PROJECT_ROOT / "data" / "inps_pensioni_decorrenza_pubblici_tutte_categorie_2026_v1.csv"
)
CUBO1_TTL = PROJECT_ROOT / "output" / "observations" / "cubo1_vigenti_residenza.ttl"
OUTPUT_TTL = PROJECT_ROOT / "output" / "observations" / "cubo9_plan_b_gdp_projected.ttl"


# Mapping regime notation (output di ProjectGDPRegimeComposition) → URI SKOS Concept
REGIME_TO_URI = {
    "retributivo":       V.REGIME_RETRIBUTIVO,
    "misto-dini":        V.REGIME_MISTO_DINI,
    "misto-fornero":     V.REGIME_MISTO_FORNERO,
    "contributivo-puro": V.REGIME_CONTRIBUTIVO_PURO,
}
# Slug per URI obs (devono essere URL-safe, no spazi)
REGIME_TO_SHORT = {
    "retributivo":       "retr",
    "misto-dini":        "mix-dini",
    "misto-fornero":     "mix-fornero",
    "contributivo-puro": "contr",
}


def _load_pubblici_per_provincia(cubo1_ttl: Path) -> pd.DataFrame:
    """Legge il cubo 1 via SPARQL ed estrae n_pubblici per provincia.

    Returns:
        DataFrame con 107 righe e colonne: uri_agid, codice_istat,
        n_pubblici (int), obs_uri_cubo1 (URI dell'obs del cubo 1).
    """
    from rdflib import Graph

    g = Graph()
    g.parse(str(cubo1_ttl), format="turtle")

    rows = []
    for binding in g.query(_q("""
        PREFIX qb: <http://purl.org/linked-data/cube#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX clv: <https://w3id.org/italia/onto/CLV/>
        PREFIX idpt: <https://example.org/idpt/>

        SELECT ?obs ?prov ?n_pubblici WHERE {
          ?obs a qb:Observation ;
               idpt:provincia ?prov ;
               idpt:tipoGestione idpt:gestione-pubblici ;
               idpt:numeroPensioni ?n_pubblici .
        }
        ORDER BY ?prov
    """)):
        rows.append({
            "obs_uri_cubo1": str(binding.obs),
            "uri_agid":      str(binding.prov),
            "n_pubblici":    int(binding.n_pubblici),
        })

    df = pd.DataFrame(rows)
    # Estraggo codice_istat dall'URI AGID (ultimo segmento)
    df["codice_istat"] = df["uri_agid"].str.rsplit("/", n=1).str[-1]
    return df


class CuboPlanBGdpRecipe(Recipe):
    """Recipe cubo 9: Plan B GDP, composizione regime stimata per provincia."""

    def build(self) -> Pipeline:
        return (
            Pipeline()
            .add(ProjectGDPRegimeComposition(
                count_column="n_pubblici",
                decorrenza_csv=DECORRENZA_CSV,
                output_shape="long",  # espande 107 → 428 righe
                keep_extra_columns=True,
            ))
            .add(EmitQbObservations(
                dataset_uri=V.CUBE_PLAN_B_GDP_PROJECTED,
                dsd_uri=V.DSD_PLAN_B_GDP_PROJECTED,
                obs_uri_template=(
                    V.IDPT_NS + "obs-plan-b-{codice_istat}-{regime_short}-2026"
                ),
                dimensions={
                    "uri_agid":    V.PROVINCIA,
                    "regime_uri":  V.REGIME_LIQUIDAZIONE,
                },
                constant_dimensions={
                    V.ANNO_RIFERIMENTO: '"2026"^^xsd:gYear',
                },
                measures={
                    "numero_pensioni_proiettato": V.NUMERO_PENSIONI,
                },
                obs_status_column="obs_status_uri",
                prov_derived_from_column="prov_derived_uris",
                dataset_metadata={
                    "title": "Plan B GDP — composizione regime stimata per provincia, 2026",
                    "description": (
                        "Cubo derivato: composizione regime delle pensioni della Gestione "
                        "Dipendenti Pubblici (GDP) per ognuna delle 107 province italiane, "
                        "ottenuta tramite proiezione uniforme della composizione regime "
                        "nazionale (stimata da euristica decorrenza→regime applicata al "
                        "cubo 4) sulle quote provinciali GDP (cubo 1, tipoGestione=Pubblici). "
                        "Tutte le obs marcate obsStatus=E + doppia prov:wasDerivedFrom "
                        "verso obs cubo 1 + DataSet cubo 4. Stima dichiarata, non misura "
                        "primaria: sostituisce dati che l'INPS non pubblica a granularità "
                        "provincia × regime per il comparto pubblico."
                    ),
                    "issued": "2026-05-29",
                    "source": "https://www.inps.it/osservatorio",
                    "license": V.LICENSE_CC_BY_4_0,
                    "rights": (
                        "Stima derivata da dati INPS via euristica documentata in "
                        "PROGETTO_CONTESTO.md sez. 10.6 e 10.14."
                    ),
                },
                output_path=OUTPUT_TTL,
            ))
        )


def main() -> int:
    if not CUBO1_TTL.exists():
        print(f"✗ Cubo 1 TTL non trovato: {CUBO1_TTL}")
        print("  Esegui prima la Recipe del cubo 1.")
        return 1
    if not DECORRENZA_CSV.exists():
        print(f"✗ CSV decorrenza non trovato: {DECORRENZA_CSV}")
        return 1

    print(f"=== Recipe Cubo 9 — Plan B GDP projected ===")
    print(f"Input cubo 1: {CUBO1_TTL}")
    print(f"Input CSV:    {DECORRENZA_CSV}")
    print(f"Output:       {OUTPUT_TTL}")
    print()

    df = _load_pubblici_per_provincia(CUBO1_TTL)
    print(f"✓ Letti dati GDP dal cubo 1: {len(df)} province con n_pubblici")
    if len(df) != 107:
        print(f"  ⚠ Atteso 107 province, trovate {len(df)}")

    # Esegui pipeline (Project + Emit)
    # Prima Project, poi post-processing inline per regime_uri/short + prov_derived_uris
    ds_intermediate = ProjectGDPRegimeComposition(
        count_column="n_pubblici",
        decorrenza_csv=DECORRENZA_CSV,
        output_shape="long",
        keep_extra_columns=True,
    ).apply(Dataset(df))
    df_long = ds_intermediate.to_pandas()

    # Post-processing: regime_uri + regime_short + prov_derived + obs_status
    df_long["regime_uri"] = df_long["regime_notation"].map(REGIME_TO_URI)
    df_long["regime_short"] = df_long["regime_notation"].map(REGIME_TO_SHORT)
    df_long["obs_status_uri"] = V.SDMX_CODE_OBS_STATUS_E
    df_long["prov_derived_uris"] = df_long["obs_uri_cubo1"].apply(
        lambda obs_cubo1: [obs_cubo1, V.CUBE_PENSIONI_DECORRENZA_GDP]
    )

    # Verifica mapping
    if df_long["regime_uri"].isna().any():
        print(f"⚠ Alcune regime_notation non mappate a URI: "
              f"{df_long[df_long['regime_uri'].isna()]['regime_notation'].unique()}")
        return 1

    print(f"✓ Pipeline Project produce {len(df_long)} righe (107 × 4 regimi = 428 atteso)")
    print(f"  Composizione regime nazionale: "
          f"{ds_intermediate.history[-1].metrics['composition_percentages']}")

    # Ora Emit (con df già arricchito)
    emit_ds = EmitQbObservations(
        dataset_uri=V.CUBE_PLAN_B_GDP_PROJECTED,
        dsd_uri=V.DSD_PLAN_B_GDP_PROJECTED,
        obs_uri_template=V.IDPT_NS + "obs-plan-b-{codice_istat}-{regime_short}-2026",
        dimensions={
            "uri_agid":   V.PROVINCIA,
            "regime_uri": V.REGIME_LIQUIDAZIONE,
        },
        constant_dimensions={
            V.ANNO_RIFERIMENTO: '"2026"^^xsd:gYear',
        },
        measures={"numero_pensioni_proiettato": V.NUMERO_PENSIONI},
        obs_status_column="obs_status_uri",
        prov_derived_from_column="prov_derived_uris",
        dataset_metadata={
            "title": "Plan B GDP — composizione regime stimata per provincia, 2026",
            "description": (
                "Cubo derivato: composizione regime delle pensioni della Gestione "
                "Dipendenti Pubblici (GDP) per ognuna delle 107 province italiane, "
                "ottenuta tramite proiezione uniforme della composizione regime "
                "nazionale (stimata da euristica decorrenza→regime applicata al "
                "cubo 4) sulle quote provinciali GDP (cubo 1, tipoGestione=Pubblici). "
                "Tutte le obs marcate obsStatus=E + doppia prov:wasDerivedFrom "
                "verso obs cubo 1 + DataSet cubo 4. Stima dichiarata."
            ),
            "issued": "2026-05-29",
            "source": "https://www.inps.it/osservatorio",
            "license": V.LICENSE_CC_BY_4_0,
            "rights": "Stima derivata via euristica documentata in PROGETTO_CONTESTO.md sez. 10.6/10.14.",
        },
        output_path=OUTPUT_TTL,
    ).apply(Dataset(df_long))

    print()
    rec = emit_ds.history[-1]
    print(f"  EmitQbObservations:")
    for k, v in rec.metrics.items():
        if isinstance(v, (list, dict)) and len(str(v)) > 80:
            print(f"        {k}: {type(v).__name__} ({len(v)} items)")
        else:
            print(f"        {k}: {v}")

    # Sanity check: somma proiezioni per provincia = n_pubblici input (conservazione)
    out = emit_ds.to_pandas()
    sums = out.groupby("codice_istat")["numero_pensioni_proiettato"].sum().round(0)
    inputs = df.set_index("codice_istat")["n_pubblici"]
    diff = (sums - inputs).abs().max()
    print()
    print(f"✓ Conservazione totali GDP per provincia: max diff = {diff} pensioni (atteso ≈ 0)")
    print(f"✓ Totale nazionale proiettato: {int(out['numero_pensioni_proiettato'].sum()):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
