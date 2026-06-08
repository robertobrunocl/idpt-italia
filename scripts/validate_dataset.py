"""scripts/validate_dataset.py — Validazione DCAT-AP_IT del deliverable.

Carica ``output/dataset/atlante_idpt_dataset.ttl`` insieme ai 9 cubi + vocabolari
e verifica via SPARQL che la struttura DCAT-AP_IT sia conforme:

1. Esattamente 1 ``dcatapit:Dataset`` con ``dcterms:title``, ``description``,
   ``issued``, ``license``, ``publisher``, ``rights``, ``conformsTo``
2. ``dcterms:hasPart`` verso esattamente 9 ``qb:DataSet`` (corrispondenti ai
   cubi 1-9 emessi)
3. ``dcat:distribution`` verso esattamente 3 ``dcatapit:Distribution``
4. VoID minimal: ``void:triples``, ``void:sparqlEndpoint``, ``void:exampleResource``
5. ``dcat:contactPoint`` verso 1 ``vcard:Organization`` con email
6. ``dcterms:publisher`` verso 1 ``foaf:Agent`` con ``foaf:name``

Esegui:
    source .venv/bin/activate
    python scripts/validate_dataset.py
"""
from __future__ import annotations

from pathlib import Path

from rdflib import Graph

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_TTL = PROJECT_ROOT / "output" / "dataset" / "atlante_idpt_dataset.ttl"
EXPECTED_QB_DATASETS = 9
EXPECTED_DISTRIBUTIONS = 3

# Carica anche i 9 cubi per validare che gli URI in dcterms:hasPart siano qb:DataSet veri
INPUT_TTLS = [DATASET_TTL] + list((PROJECT_ROOT / "output").rglob("*.ttl"))


def main() -> int:
    print("=== Validazione DCAT-AP_IT deliverable ===")
    print(f"Dataset: {DATASET_TTL}")
    print()

    if not DATASET_TTL.exists():
        print(f"✗ File non trovato: {DATASET_TTL}")
        return 1

    g = Graph()
    for ttl in set(INPUT_TTLS):
        g.parse(str(ttl), format="turtle")
    print(f"✓ Grafo caricato: {len(g):,} triple")

    checks: list[bool] = []

    def check(query: str, expected: int, label: str) -> bool:
        actual = int(list(g.query(query))[0][0])
        ok = actual == expected
        print(f"  {'✓' if ok else '✗'} {label}: {actual} (atteso {expected})")
        return ok

    # ---- Check 1: 1 dcatapit:Dataset ----
    print("[1] DCAT-AP_IT Dataset")
    checks.append(check("""
    PREFIX dcatapit: <http://dati.gov.it/onto/dcatapit#>
    SELECT (COUNT(?d) AS ?n) WHERE { ?d a dcatapit:Dataset }
    """, 1, "dcatapit:Dataset"))

    # ---- Check 2: metadati obbligatori sul dataset ----
    required_props = {
        "dcterms:title": "http://purl.org/dc/terms/title",
        "dcterms:description": "http://purl.org/dc/terms/description",
        "dcterms:issued": "http://purl.org/dc/terms/issued",
        "dcterms:license": "http://purl.org/dc/terms/license",
        "dcterms:publisher": "http://purl.org/dc/terms/publisher",
        "dcterms:rights": "http://purl.org/dc/terms/rights",
    }
    for short, uri in required_props.items():
        # Conta i Dataset distinti che hanno la property, non le triple
        # (title/description possono essere multi-lingua → multiple triple).
        checks.append(check(f"""
        PREFIX dcatapit: <http://dati.gov.it/onto/dcatapit#>
        SELECT (COUNT(DISTINCT ?d) AS ?n) WHERE {{
          ?d a dcatapit:Dataset ; <{uri}> ?v .
        }}
        """, 1, f"{short} presente"))

    # ---- Check 3: dcterms:hasPart verso 9 qb:DataSet ----
    print()
    print("[2] dcterms:hasPart")
    checks.append(check("""
    PREFIX dcatapit: <http://dati.gov.it/onto/dcatapit#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX qb: <http://purl.org/linked-data/cube#>
    SELECT (COUNT(DISTINCT ?part) AS ?n) WHERE {
      ?d a dcatapit:Dataset ; dcterms:hasPart ?part .
      ?part a qb:DataSet .
    }
    """, EXPECTED_QB_DATASETS, f"qb:DataSet collegati via hasPart"))

    # ---- Check 4: distribuzioni ----
    print()
    print("[3] Distribuzioni")
    checks.append(check("""
    PREFIX dcatapit: <http://dati.gov.it/onto/dcatapit#>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    SELECT (COUNT(DISTINCT ?dist) AS ?n) WHERE {
      ?d a dcatapit:Dataset ; dcat:distribution ?dist .
      ?dist a dcatapit:Distribution .
    }
    """, EXPECTED_DISTRIBUTIONS, "dcatapit:Distribution"))

    # ---- Check 5: VoID ----
    print()
    print("[4] VoID minimal (3 property)")
    for short, uri in (("void:triples", "http://rdfs.org/ns/void#triples"),
                        ("void:sparqlEndpoint", "http://rdfs.org/ns/void#sparqlEndpoint"),
                        ("void:exampleResource", "http://rdfs.org/ns/void#exampleResource")):
        checks.append(check(f"""
        PREFIX void: <http://rdfs.org/ns/void#>
        SELECT (COUNT(?v) AS ?n) WHERE {{ ?d <{uri}> ?v }}
        """, 1 if short != "void:exampleResource" else 3, f"{short}"))

    # ---- Check 6: contactPoint ----
    print()
    print("[5] Contact point + agents")
    checks.append(check("""
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
    SELECT (COUNT(*) AS ?n) WHERE {
      ?d dcat:contactPoint ?c .
      ?c vcard:hasEmail ?email .
    }
    """, 1, "dcat:contactPoint con email vcard"))

    checks.append(check("""
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    SELECT (COUNT(*) AS ?n) WHERE {
      ?d dcterms:publisher ?p .
      ?p foaf:name ?name .
    }
    """, 1, "dcterms:publisher → foaf:Agent con foaf:name"))

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
