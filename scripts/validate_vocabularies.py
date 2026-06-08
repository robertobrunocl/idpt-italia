"""scripts/validate_vocabularies.py — Validazione dei TTL di vocabolario.

Carica `output/vocabularies/code_lists.ttl` + `output/vocabularies/classes_and_properties.ttl`
in un grafo rdflib in-memory e verifica con SPARQL che la struttura sia
conforme al check-point ontologico (sez. 10.10 + 10.11 + 10.12 di
PROGETTO_CONTESTO.md):

1. 6 `skos:ConceptScheme` (5 principali + 1 ausiliaria aree-geografiche)
2. 27 `skos:Concept` totali nei 6 schemi (5+4+8+5+4+1)
3. 1 sola `owl:Class` propria (`idpt:SedeINPS`)
4. 9 `qb:DataStructureDefinition`, una per cubo
5. Ogni DSD ha almeno 1 dimensione + 1 misura (well-formed cube semplificato)
6. Le `qb:DimensionProperty` con range `skos:Concept` hanno `qb:codeList`
   verso una `skos:ConceptScheme` definita nel grafo
7. Le `qb:MeasureProperty` hanno `qb:concept` sdmx-concept

Esegui da root progetto:
    source .venv/bin/activate
    python scripts/validate_vocabularies.py

Exit code 0 se tutti i check passano, 1 altrimenti.
"""
from __future__ import annotations

from pathlib import Path

from rdflib import Graph

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CODE_LISTS_TTL = PROJECT_ROOT / "output" / "vocabularies" / "code_lists.ttl"
CLASSES_TTL = PROJECT_ROOT / "output" / "vocabularies" / "classes_and_properties.ttl"

# Costanti attese dal check-point ontologico
EXPECTED_CONCEPT_SCHEMES = 6
EXPECTED_CONCEPTS_TOTAL = 27         # 5 + 4 + 8 + 5 + 4 + 1
EXPECTED_OWL_CLASSES = 1             # solo idpt:SedeINPS
EXPECTED_DSDS = 9
EXPECTED_OBJECT_PROPERTIES = 2       # correspondsToProvinceAGID + aggregatesProvince
EXPECTED_DIMENSION_PROPERTIES_MIN = 10
EXPECTED_MEASURE_PROPERTIES_MIN = 9


def load_graph() -> Graph:
    """Carica entrambi i TTL in un unico grafo in-memory."""
    if not CODE_LISTS_TTL.exists():
        raise FileNotFoundError(CODE_LISTS_TTL)
    if not CLASSES_TTL.exists():
        raise FileNotFoundError(CLASSES_TTL)
    g = Graph()
    g.parse(str(CODE_LISTS_TTL), format="turtle")
    g.parse(str(CLASSES_TTL), format="turtle")
    return g


def check_count(g: Graph, query: str, expected: int, label: str) -> bool:
    rows = list(g.query(query))
    actual = int(rows[0][0]) if rows else 0
    ok = actual == expected
    sym = "✓" if ok else "✗"
    print(f"  {sym} {label}: {actual} (atteso {expected})")
    return ok


def check_min(g: Graph, query: str, min_value: int, label: str) -> bool:
    rows = list(g.query(query))
    actual = int(rows[0][0]) if rows else 0
    ok = actual >= min_value
    sym = "✓" if ok else "✗"
    print(f"  {sym} {label}: {actual} (atteso ≥ {min_value})")
    return ok


def check_well_formed_cube(g: Graph) -> bool:
    """Check semplificato qb:WellFormedCube: ogni DSD ha ≥1 dimensione + ≥1 misura."""
    bad_dsds = list(g.query("""
    PREFIX qb: <http://purl.org/linked-data/cube#>
    SELECT ?dsd WHERE {
      ?dsd a qb:DataStructureDefinition .
      OPTIONAL {
        ?dsd qb:component [ qb:dimension ?dim ] .
      }
      OPTIONAL {
        ?dsd qb:component [ qb:measure ?meas ] .
      }
      FILTER(!BOUND(?dim) || !BOUND(?meas))
    }
    """))
    if not bad_dsds:
        print(f"  ✓ Tutte le DSD hanno ≥1 dimensione e ≥1 misura")
        return True
    print(f"  ✗ DSD malformate: {len(bad_dsds)}")
    for r in bad_dsds:
        print(f"      {r[0]}")
    return False


def check_dimension_code_list_link(g: Graph) -> bool:
    """Ogni DimensionProperty con range skos:Concept deve avere qb:codeList."""
    bad = list(g.query("""
    PREFIX qb:   <http://purl.org/linked-data/cube#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?dim WHERE {
      ?dim a qb:DimensionProperty ;
           rdfs:range skos:Concept .
      FILTER NOT EXISTS { ?dim qb:codeList ?cs }
    }
    """))
    if not bad:
        print("  ✓ Tutte le DimensionProperty con range skos:Concept hanno qb:codeList")
        return True
    print(f"  ✗ Dimension property senza qb:codeList: {len(bad)}")
    for r in bad:
        print(f"      {r[0]}")
    return False


def check_measure_sdmx_concept(g: Graph) -> bool:
    """Ogni MeasureProperty deve avere qb:concept verso sdmx-concept."""
    bad = list(g.query("""
    PREFIX qb: <http://purl.org/linked-data/cube#>
    SELECT ?meas WHERE {
      ?meas a qb:MeasureProperty .
      FILTER NOT EXISTS { ?meas qb:concept ?c }
    }
    """))
    if not bad:
        print("  ✓ Tutte le MeasureProperty hanno qb:concept (interoperabilità SDMX)")
        return True
    print(f"  ✗ Measure property senza qb:concept: {len(bad)}")
    for r in bad:
        print(f"      {r[0]}")
    return False


def main() -> int:
    print("=== Validazione vocabularies ===")
    print(f"code_lists.ttl:           {CODE_LISTS_TTL}")
    print(f"classes_and_properties.ttl: {CLASSES_TTL}")
    print()

    g = load_graph()
    print(f"✓ Grafo caricato: {len(g):,} triple")
    print()

    checks: list[bool] = []

    # ---- Check 1: 6 ConceptScheme ----
    print("[1] Code-list (skos:ConceptScheme)")
    checks.append(check_count(g,
        """PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
           SELECT (COUNT(DISTINCT ?cs) AS ?n) WHERE { ?cs a skos:ConceptScheme }""",
        EXPECTED_CONCEPT_SCHEMES, "ConceptScheme totali"))

    # ---- Check 2: 27 Concept ----
    checks.append(check_count(g,
        """PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
           SELECT (COUNT(DISTINCT ?c) AS ?n) WHERE { ?c a skos:Concept }""",
        EXPECTED_CONCEPTS_TOTAL, "Concept totali"))

    # ---- Check 3: 1 owl:Class propria ----
    print()
    print("[2] Classi proprie")
    checks.append(check_count(g,
        """PREFIX owl: <http://www.w3.org/2002/07/owl#>
           SELECT (COUNT(DISTINCT ?cls) AS ?n) WHERE { ?cls a owl:Class }""",
        EXPECTED_OWL_CLASSES, "owl:Class propria"))

    checks.append(check_count(g,
        """PREFIX owl: <http://www.w3.org/2002/07/owl#>
           SELECT (COUNT(DISTINCT ?p) AS ?n) WHERE { ?p a owl:ObjectProperty }""",
        EXPECTED_OBJECT_PROPERTIES, "owl:ObjectProperty proprie"))

    # ---- Check 4: 9 DSD ----
    print()
    print("[3] Data Cube DSD")
    checks.append(check_count(g,
        """PREFIX qb: <http://purl.org/linked-data/cube#>
           SELECT (COUNT(DISTINCT ?d) AS ?n) WHERE { ?d a qb:DataStructureDefinition }""",
        EXPECTED_DSDS, "qb:DataStructureDefinition"))

    # ---- Check 5: Well-formed cube semplificato ----
    checks.append(check_well_formed_cube(g))

    # ---- Check 6: DimensionProperty / MeasureProperty count ----
    print()
    print("[4] Dimension/Measure property")
    checks.append(check_min(g,
        """PREFIX qb: <http://purl.org/linked-data/cube#>
           SELECT (COUNT(DISTINCT ?p) AS ?n) WHERE { ?p a qb:DimensionProperty }""",
        EXPECTED_DIMENSION_PROPERTIES_MIN, "qb:DimensionProperty"))
    checks.append(check_min(g,
        """PREFIX qb: <http://purl.org/linked-data/cube#>
           SELECT (COUNT(DISTINCT ?p) AS ?n) WHERE { ?p a qb:MeasureProperty }""",
        EXPECTED_MEASURE_PROPERTIES_MIN, "qb:MeasureProperty"))

    # ---- Check 7 + 8: Linking property→codelist e measure→sdmx-concept ----
    print()
    print("[5] Linking di interoperabilità")
    checks.append(check_dimension_code_list_link(g))
    checks.append(check_measure_sdmx_concept(g))

    # ---- Riepilogo ----
    print()
    passed = sum(checks)
    total = len(checks)
    if passed == total:
        print(f"=== Tutti i check passati: {passed}/{total} ===")
        return 0
    print(f"=== Falliti: {total - passed}/{total} ===")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
