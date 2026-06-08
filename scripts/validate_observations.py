"""scripts/validate_observations.py — Validazione dei cubi emessi.

Per ciascuno dei 9 cubi del progetto, verifica tramite query SPARQL che
``output/observations/cuboN_*.ttl`` (o ``output/computed/cubo8_*.ttl`` per il
cubo IDPT) contenga:

- 1 ``qb:DataSet`` con ``qb:structure`` verso la DSD corretta (in
  ``output/vocabularies/classes_and_properties.ttl``)
- N ``qb:Observation`` (cardinalità attesa per cubo)
- Ogni obs ha tutte le dimensioni della DSD + tutte le misure
- Ogni obs ha ``sdmx-attribute:obsStatus``

Validation incrementale: i cubi non ancora emessi vengono saltati con un
warning. La pipeline cresce man mano che chiudiamo le Recipe.

Esegui da root progetto:
    source .venv/bin/activate
    python scripts/validate_observations.py

Exit code 0 se tutti i check passano, 1 altrimenti.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rdflib import Graph

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VOCABS_DIR = PROJECT_ROOT / "output" / "vocabularies"
OBS_DIR = PROJECT_ROOT / "output" / "observations"
COMPUTED_DIR = PROJECT_ROOT / "output" / "computed"


# =============================================================================
# Configurazione cubi attesi
# =============================================================================

@dataclass
class CubeSpec:
    """Specifiche di un cubo per la validazione."""
    name: str
    file_path: Path
    dataset_uri: str
    dsd_uri: str
    expected_observations: int
    required_dimensions: list[str]  # URI delle property dimension attese
    required_measures: list[str]    # URI delle property measure attese (almeno una per obs)
    measures_per_obs_min: int = 1   # quante measure per obs (stile A o B)


IDPT_NS = "https://example.org/idpt/"

CUBE_SPECS: list[CubeSpec] = [
    # Cubo 1 — pensioni-vigenti-residenza (stile A, 3 measure per obs)
    CubeSpec(
        name="Cubo 1 — pensioni-vigenti-residenza",
        file_path=OBS_DIR / "cubo1_vigenti_residenza.ttl",
        dataset_uri=IDPT_NS + "cubo-pensioni-vigenti-residenza",
        dsd_uri=IDPT_NS + "dsd-pensioni-vigenti-residenza",
        expected_observations=535,
        required_dimensions=[
            IDPT_NS + "provincia",
            IDPT_NS + "annoRiferimento",
            IDPT_NS + "tipoGestione",
        ],
        required_measures=[
            IDPT_NS + "numeroPensioni",
            IDPT_NS + "importoMedioMensile",
            IDPT_NS + "importoAnnuoComplessivo",
        ],
        measures_per_obs_min=3,
    ),
    # Cubo 2 — pensioni-regime-sede (stile B, 1 measure per obs).
    # DSD aggiornata in Fase 5: rimossa dimensione tipoGestione (cubo OLAP
    # INPS aggrega già Privati+Autonomi/Parasub, esclude Pubblici).
    # Cardinalità: 106 sedi × 1 anno × 4 regimi × 3 measureType = 1.272 obs.
    CubeSpec(
        name="Cubo 2 — pensioni-regime-sede",
        file_path=OBS_DIR / "cubo2_regime_sede.ttl",
        dataset_uri=IDPT_NS + "cubo-pensioni-regime-sede",
        dsd_uri=IDPT_NS + "dsd-pensioni-regime-sede",
        expected_observations=1272,
        required_dimensions=[
            IDPT_NS + "sedeINPS",
            IDPT_NS + "annoRiferimento",
            IDPT_NS + "regimeLiquidazione",
        ],
        required_measures=[],  # stile B → measure individuale per obs via qb:measureType
        measures_per_obs_min=1,
    ),
    # Cubo 3 — serie-storica-sede (stile B). Cardinalità rivista in Fase 5:
    # il CSV ha già aggregato le 4 gestioni come gestione-totale (60 colonne =
    # 29 anni × 2 misure). 106 × 29 × 3 measureType - ~99 obs scartate per
    # BAT/Fermo/Monza 1998-2008 (celle "-") = ~9.123 obs (margine: 8.000-9.500).
    CubeSpec(
        name="Cubo 3 — pensioni-serie-storica-sede",
        file_path=OBS_DIR / "cubo3_serie_storica_sede.ttl",
        dataset_uri=IDPT_NS + "cubo-pensioni-serie-storica-sede",
        dsd_uri=IDPT_NS + "dsd-pensioni-serie-storica-sede",
        expected_observations=9105,
        required_dimensions=[
            IDPT_NS + "sedeINPS",
            IDPT_NS + "annoRiferimento",
            IDPT_NS + "tipoGestione",
        ],
        required_measures=[],
        measures_per_obs_min=1,
    ),
    # Cubo 4 — decorrenza-gdp (stile A, 3 measure)
    CubeSpec(
        name="Cubo 4 — pensioni-decorrenza-gdp",
        file_path=OBS_DIR / "cubo4_decorrenza_gdp.ttl",
        dataset_uri=IDPT_NS + "cubo-pensioni-decorrenza-gdp",
        dsd_uri=IDPT_NS + "dsd-pensioni-decorrenza-gdp",
        expected_observations=46,
        required_dimensions=[
            IDPT_NS + "areaGeografica",
            IDPT_NS + "annoDecorrenza",
        ],
        required_measures=[
            IDPT_NS + "numeroPensioni",
            IDPT_NS + "importoMedioMensile",
            IDPT_NS + "etaMediaDecorrenza",
        ],
        measures_per_obs_min=1,  # non tutte le obs hanno tutte le measure
    ),
    # Cubo 5 — occupati-istat (stile A, 1 measure)
    CubeSpec(
        name="Cubo 5 — occupati-istat",
        file_path=OBS_DIR / "cubo5_occupati_istat.ttl",
        dataset_uri=IDPT_NS + "cubo-occupati-istat",
        dsd_uri=IDPT_NS + "dsd-occupati-istat",
        expected_observations=107,
        required_dimensions=[
            IDPT_NS + "provincia",
            IDPT_NS + "annoRiferimento",
        ],
        required_measures=[IDPT_NS + "numeroOccupati"],
        measures_per_obs_min=1,
    ),
    # Cubo 6 — indicatori-demografici-istat (stile A, 1 measure)
    CubeSpec(
        name="Cubo 6 — indicatori-demografici-istat",
        file_path=OBS_DIR / "cubo6_indicatori_demografici_istat.ttl",
        dataset_uri=IDPT_NS + "cubo-indicatori-demografici-istat",
        dsd_uri=IDPT_NS + "dsd-indicatori-demografici-istat",
        expected_observations=856,
        required_dimensions=[
            IDPT_NS + "provincia",
            IDPT_NS + "annoRiferimento",
            IDPT_NS + "indicatoreDemografico",
        ],
        required_measures=[IDPT_NS + "valoreIndicatore"],
        measures_per_obs_min=1,
    ),
    # Cubo 7 — redditi-mef (stile A, 2 measure)
    CubeSpec(
        name="Cubo 7 — redditi-mef",
        file_path=OBS_DIR / "cubo7_redditi_mef.ttl",
        dataset_uri=IDPT_NS + "cubo-redditi-mef",
        dsd_uri=IDPT_NS + "dsd-redditi-mef",
        expected_observations=535,
        required_dimensions=[
            IDPT_NS + "provincia",
            IDPT_NS + "annoRiferimento",
            IDPT_NS + "voceReddito",
        ],
        required_measures=[
            IDPT_NS + "frequenzaDichiaranti",
            IDPT_NS + "ammontareTotale",
        ],
        measures_per_obs_min=2,
    ),
    # Cubo 8 — idpt-computed (stile A, 1 measure)
    CubeSpec(
        name="Cubo 8 — idpt-computed",
        file_path=COMPUTED_DIR / "cubo8_idpt_computed.ttl",
        dataset_uri=IDPT_NS + "cubo-idpt-computed",
        dsd_uri=IDPT_NS + "dsd-idpt-computed",
        expected_observations=428,
        required_dimensions=[
            IDPT_NS + "provincia",
            IDPT_NS + "annoRiferimento",
            IDPT_NS + "componenteIDPT",
        ],
        required_measures=[IDPT_NS + "valoreIDPT"],
        measures_per_obs_min=1,
    ),
    # Cubo 9 — plan-b-gdp-projected (stile A, 1 measure)
    CubeSpec(
        name="Cubo 9 — plan-b-gdp-projected",
        file_path=OBS_DIR / "cubo9_plan_b_gdp_projected.ttl",
        dataset_uri=IDPT_NS + "cubo-plan-b-gdp-projected",
        dsd_uri=IDPT_NS + "dsd-plan-b-gdp-projected",
        expected_observations=428,
        required_dimensions=[
            IDPT_NS + "provincia",
            IDPT_NS + "annoRiferimento",
            IDPT_NS + "regimeLiquidazione",
        ],
        required_measures=[IDPT_NS + "numeroPensioni"],
        measures_per_obs_min=1,
    ),
]


# =============================================================================
# Validazione di un singolo cubo
# =============================================================================

def validate_cube(spec: CubeSpec) -> tuple[bool, list[str]]:
    """Ritorna (passed, messages)."""
    msgs: list[str] = []
    all_ok = True

    if not spec.file_path.exists():
        msgs.append(f"  ⚠ SKIP — file non esiste: {spec.file_path}")
        return True, msgs  # Skip = non blocca la pipeline

    # Carico cubo + vocabolari (per riferire DSD)
    g = Graph()
    g.parse(str(spec.file_path), format="turtle")
    for vocab in VOCABS_DIR.glob("*.ttl"):
        g.parse(str(vocab), format="turtle")

    # Check 1: 1 qb:DataSet con URI atteso
    rows = list(g.query(f"""
    PREFIX qb: <http://purl.org/linked-data/cube#>
    SELECT (COUNT(?d) AS ?n) WHERE {{
      <{spec.dataset_uri}> a qb:DataSet ;
                           qb:structure <{spec.dsd_uri}> .
      BIND(<{spec.dataset_uri}> AS ?d)
    }}
    """))
    if int(rows[0][0]) == 1:
        msgs.append(f"  ✓ qb:DataSet con DSD corretta")
    else:
        msgs.append(f"  ✗ qb:DataSet/DSD mismatch")
        all_ok = False

    # Check 2: numero observation
    rows = list(g.query(f"""
    PREFIX qb: <http://purl.org/linked-data/cube#>
    SELECT (COUNT(?o) AS ?n) WHERE {{
      ?o a qb:Observation ;
         qb:dataSet <{spec.dataset_uri}> .
    }}
    """))
    actual_obs = int(rows[0][0])
    if actual_obs == spec.expected_observations:
        msgs.append(f"  ✓ {actual_obs}/{spec.expected_observations} observation")
    else:
        msgs.append(f"  ✗ {actual_obs} observation (atteso {spec.expected_observations})")
        all_ok = False

    # Check 3: ogni obs ha tutte le dimensioni richieste
    for dim_uri in spec.required_dimensions:
        rows = list(g.query(f"""
        PREFIX qb: <http://purl.org/linked-data/cube#>
        SELECT (COUNT(?o) AS ?n) WHERE {{
          ?o a qb:Observation ;
             qb:dataSet <{spec.dataset_uri}> .
          FILTER NOT EXISTS {{ ?o <{dim_uri}> ?v }}
        }}
        """))
        missing = int(rows[0][0])
        short_dim = dim_uri.rsplit("/", 1)[-1]
        if missing == 0:
            msgs.append(f"  ✓ tutte le obs hanno {short_dim}")
        else:
            msgs.append(f"  ✗ {missing} obs senza {short_dim}")
            all_ok = False

    # Check 4: ogni obs ha obsStatus
    rows = list(g.query(f"""
    PREFIX qb: <http://purl.org/linked-data/cube#>
    PREFIX sdmx-attribute: <http://purl.org/linked-data/sdmx/2009/attribute#>
    SELECT (COUNT(?o) AS ?n) WHERE {{
      ?o a qb:Observation ;
         qb:dataSet <{spec.dataset_uri}> .
      FILTER NOT EXISTS {{ ?o sdmx-attribute:obsStatus ?s }}
    }}
    """))
    missing_status = int(rows[0][0])
    if missing_status == 0:
        msgs.append(f"  ✓ tutte le obs hanno sdmx-attribute:obsStatus")
    else:
        msgs.append(f"  ✗ {missing_status} obs senza obsStatus")
        all_ok = False

    # Check 5: ogni obs ha almeno measures_per_obs_min misure
    if spec.required_measures and spec.measures_per_obs_min > 0:
        # Costruisco SPARQL che conta le measure per obs e verifica ≥ min
        rows = list(g.query(f"""
        PREFIX qb: <http://purl.org/linked-data/cube#>
        SELECT (COUNT(DISTINCT ?o) AS ?n) WHERE {{
          ?o a qb:Observation ;
             qb:dataSet <{spec.dataset_uri}> .
          {{
            SELECT ?o (COUNT(?m) AS ?nMeas) WHERE {{
              ?o a qb:Observation ;
                 qb:dataSet <{spec.dataset_uri}> .
              VALUES ?meas {{ { ' '.join(f'<{m}>' for m in spec.required_measures) } }}
              ?o ?meas ?v .
              BIND(?meas AS ?m)
            }}
            GROUP BY ?o
            HAVING (COUNT(?m) >= {spec.measures_per_obs_min})
          }}
        }}
        """))
        ok_obs = int(rows[0][0])
        if ok_obs == actual_obs:
            msgs.append(
                f"  ✓ tutte le obs hanno ≥{spec.measures_per_obs_min} misure dichiarate"
            )
        else:
            msgs.append(
                f"  ✗ solo {ok_obs}/{actual_obs} obs hanno ≥{spec.measures_per_obs_min} misure"
            )
            all_ok = False

    return all_ok, msgs


# =============================================================================
# Main
# =============================================================================

def main() -> int:
    print("=== Validazione cubi emessi ===")
    print(f"Vocabularies: {VOCABS_DIR}")
    print(f"Observations: {OBS_DIR}")
    print()

    if not VOCABS_DIR.exists():
        print(f"✗ Cartella vocabularies non trovata: {VOCABS_DIR}")
        return 1

    total = 0
    passed = 0
    skipped = 0
    failed_cubes: list[str] = []

    for spec in CUBE_SPECS:
        print(f"[{spec.name}]")
        ok, msgs = validate_cube(spec)
        for m in msgs:
            print(m)
        if not spec.file_path.exists():
            skipped += 1
        else:
            total += 1
            if ok:
                passed += 1
            else:
                failed_cubes.append(spec.name)
        print()

    print(f"=== Riepilogo ===")
    print(f"Cubi validati: {passed}/{total}")
    if skipped:
        print(f"Cubi non ancora emessi: {skipped}")
    if failed_cubes:
        print(f"Falliti: {failed_cubes}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
