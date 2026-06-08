"""scripts/generate_agid_to_dbpedia.py — Genera output/mappings/agid_to_dbpedia.ttl

Esegue una query SPARQL su DBpedia per recuperare le risorse delle province
italiane (e città metropolitane), le riconcilia con le 107 province AGID
tramite match esatto su prefLabel + dizionario manuale per le anomalie note,
e materializza il risultato come sidecar TTL con 107 triple
``owl:sameAs`` (più header di provenance ``prov:Entity``).

Pianificato in Fase 2 (PROGETTO_CONTESTO.md sez. 10.13). Esecuzione una tantum
lato Mac (richiede rete verso `https://dbpedia.org/sparql`).

Uso:
    source .venv/bin/activate
    python scripts/generate_agid_to_dbpedia.py \
        --provinces-ttl data/provinces.ttl \
        --out-ttl output/mappings/agid_to_dbpedia.ttl

Opzioni:
    --dry-run    Stampa lo stato del match senza scrivere il file.
    --strict     Esce con errore se non si raggiunge 107/107 match.
"""
from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path
from typing import Iterable

# Aggiungo il pacchetto macrorefine al path se eseguito da scripts/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "macrorefine" / "src"))

from macrorefine.steps.lod.link import _normalize_province_name  # noqa: E402


# =============================================================================
# Configurazione
# =============================================================================

DBPEDIA_SPARQL_ENDPOINT = "https://dbpedia.org/sparql"

# Query SPARQL per recuperare province e città metropolitane italiane.
# DBpedia modella alcune entità come `dbo:Province`, le 14 città metropolitane
# come `dbo:MetropolitanCity` (o varianti). UNION cattura entrambi i pattern.
DBPEDIA_QUERY = """
PREFIX dbo:  <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dbr:  <http://dbpedia.org/resource/>

SELECT DISTINCT ?resource ?label_it ?label_en
WHERE {
  {
    ?resource a dbo:Province ;
              dbo:country dbr:Italy .
  } UNION {
    ?resource a dbo:AdministrativeRegion ;
              dbo:country dbr:Italy .
    FILTER(CONTAINS(LCASE(STR(?resource)), "province") ||
           CONTAINS(LCASE(STR(?resource)), "metropolitan"))
  } UNION {
    ?resource a yago:WikicatProvincesOfItaly .
  }
  OPTIONAL { ?resource rdfs:label ?label_it . FILTER(LANG(?label_it) = "it") }
  OPTIONAL { ?resource rdfs:label ?label_en . FILTER(LANG(?label_en) = "en") }
}
LIMIT 500
"""

# Dizionario manuale per le anomalie note di reconciliation AGID ↔ DBpedia.
# Chiave = codice ISTAT AGID, valore = URI DBpedia.
# Da popolare iterativamente: prima esecuzione → report unmatched → editing
# manuale di questo dizionario → seconda esecuzione → 107/107.
DBPEDIA_MANUAL_OVERRIDES: dict[str, str] = {
    # Città metropolitane (14): DBpedia spesso le modella come
    # "Metropolitan_City_of_X" anziché "Province_of_X".
    "001": "http://dbpedia.org/resource/Metropolitan_City_of_Turin",
    "010": "http://dbpedia.org/resource/Metropolitan_City_of_Genoa",
    "015": "http://dbpedia.org/resource/Metropolitan_City_of_Milan",
    "027": "http://dbpedia.org/resource/Metropolitan_City_of_Venice",
    "037": "http://dbpedia.org/resource/Metropolitan_City_of_Bologna",
    "048": "http://dbpedia.org/resource/Metropolitan_City_of_Florence",
    "058": "http://dbpedia.org/resource/Metropolitan_City_of_Rome_Capital",
    "063": "http://dbpedia.org/resource/Metropolitan_City_of_Naples",
    "072": "http://dbpedia.org/resource/Metropolitan_City_of_Bari",
    "080": "http://dbpedia.org/resource/Metropolitan_City_of_Reggio_Calabria",
    "082": "http://dbpedia.org/resource/Metropolitan_City_of_Palermo",
    "083": "http://dbpedia.org/resource/Metropolitan_City_of_Messina",
    "087": "http://dbpedia.org/resource/Metropolitan_City_of_Catania",
    "092": "http://dbpedia.org/resource/Metropolitan_City_of_Cagliari",
    # Anomalie nominali (DBpedia usa "Province of" + nome inglese che diverge
    # dalla label italiana AGID).
    "021": "http://dbpedia.org/resource/Province_of_Bolzano",   # Bolzano/Bozen
    "022": "http://dbpedia.org/resource/Province_of_Trento",    # Trento (Trentino)
    "035": "http://dbpedia.org/resource/Province_of_Reggio_Emilia",
    "040": "http://dbpedia.org/resource/Province_of_Forl%C3%AC-Cesena",
    "045": "http://dbpedia.org/resource/Province_of_Massa_and_Carrara",
    "103": "http://dbpedia.org/resource/Province_of_Verbano-Cusio-Ossola",
    "110": "http://dbpedia.org/resource/Province_of_Barletta-Andria-Trani",
    "007": "http://dbpedia.org/resource/Aosta_Valley",          # PA, valle/regione
    "111": "http://dbpedia.org/resource/Province_of_South_Sardinia",
    "108": "http://dbpedia.org/resource/Province_of_Monza_and_Brianza",
    "109": "http://dbpedia.org/resource/Province_of_Fermo",
    # 5 anomalie scoperte alla seconda iterazione (29 maggio 2026): queste province
    # non vengono restituite dalla query SPARQL come `dbo:Province + dbo:country=Italy`
    # (probabilmente tag tassonomico mancante in DBpedia). Le URI canoniche
    # `Province_of_X` esistono comunque su DBpedia e sono verificabili manualmente.
    "012": "http://dbpedia.org/resource/Province_of_Varese",
    "014": "http://dbpedia.org/resource/Province_of_Sondrio",
    "075": "http://dbpedia.org/resource/Province_of_Lecce",
    "097": "http://dbpedia.org/resource/Province_of_Lecco",
    "100": "http://dbpedia.org/resource/Province_of_Prato",
}


# =============================================================================
# Funzioni — separabili e testabili
# =============================================================================


def load_agid_provinces(provinces_ttl: Path) -> dict[str, dict[str, str]]:
    """Legge il TTL AGID e ritorna {codice_istat: {uri_agid, prefLabel}}."""
    from rdflib import Graph

    g = Graph()
    g.parse(str(provinces_ttl), format="turtle")
    out: dict[str, dict[str, str]] = {}
    for prov, label, notation in g.query("""
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX clv:  <https://w3id.org/italia/onto/CLV/>
        SELECT DISTINCT ?prov ?label ?notation WHERE {
          ?prov a clv:Province ;
                skos:prefLabel ?label ;
                skos:notation ?notation .
          FILTER(LANG(?label) = "it")
        }
    """):
        out[str(notation)] = {"uri_agid": str(prov), "prefLabel": str(label)}
    return out


def query_dbpedia_italian_provinces(
    endpoint: str = DBPEDIA_SPARQL_ENDPOINT,
    timeout_sec: int = 30,
) -> list[dict[str, str]]:
    """Esegue la query SPARQL su DBpedia. Ritorna lista di dict con keys
    `resource`, `label_it`, `label_en`. Solleva se la rete fallisce."""
    from SPARQLWrapper import SPARQLWrapper, JSON

    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(DBPEDIA_QUERY)
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(timeout_sec)
    response = sparql.query().convert()

    results = []
    for binding in response["results"]["bindings"]:
        results.append({
            "resource": binding["resource"]["value"],
            "label_it": binding.get("label_it", {}).get("value", ""),
            "label_en": binding.get("label_en", {}).get("value", ""),
        })
    return results


# Prefissi che DBpedia premette ai nomi delle province italiane sia in italiano
# sia in inglese. Strippati prima del match per riconciliare correttamente
# (es. "Province of Vercelli" → "vercelli" → match con AGID "Vercelli").
DBPEDIA_PREFIXES_TO_STRIP = (
    "provincia di ",
    "province of ",
    "metropolitan city of ",
    "citta metropolitana di ",          # post-NFKD: "città" → "citta"
    "free municipal consortium of ",    # province siciliane post-2014
    "consorzio comunale libero di ",
    "libero consorzio comunale di ",
    "regional decentralization entity of ",
)


def _strip_dbpedia_prefix(label_norm: str) -> str:
    """Rimuove i prefissi DBpedia comuni dal nome di provincia normalizzato."""
    for prefix in DBPEDIA_PREFIXES_TO_STRIP:
        if label_norm.startswith(prefix):
            return label_norm[len(prefix):].strip()
    return label_norm


def _equivalent_forms(label_norm: str) -> set[str]:
    """Genera tutte le forme equivalenti di un nome normalizzato, gestendo
    la variazione " e " ↔ " and " (italiana vs inglese, es. "Pesaro e Urbino"
    vs "Pesaro and Urbino")."""
    forms = {label_norm}
    if " and " in label_norm:
        forms.add(label_norm.replace(" and ", " e "))
    if " e " in label_norm:
        forms.add(label_norm.replace(" e ", " and "))
    return forms


def reconcile_dbpedia_to_agid(
    dbpedia_rows: Iterable[dict[str, str]],
    agid_provinces: dict[str, dict[str, str]],
    manual_overrides: dict[str, str] | None = None,
) -> tuple[dict[str, str], list[str]]:
    """Riconcilia risorse DBpedia con codici ISTAT AGID.

    Strategia:
    1. Per ogni risorsa DBpedia: estrai entrambe le label (it+en), normalizza,
       strippa i prefissi `Province of`, `Provincia di`, `Metropolitan City of`,
       ecc. Index `nome_core → URI`.
    2. Per ogni provincia AGID: normalizza prefLabel, genera forme equivalenti
       (" e " ↔ " and "), cerca match nell'index.
    3. `DBPEDIA_MANUAL_OVERRIDES` ha priorità su tutto.

    Args:
        dbpedia_rows: lista di dict da `query_dbpedia_italian_provinces`.
        agid_provinces: dict da `load_agid_provinces`.
        manual_overrides: dict {codice_istat: uri_dbpedia} per anomalie note.
            Default: DBPEDIA_MANUAL_OVERRIDES.

    Returns:
        (mapping, unmatched_istat) — mapping {codice_istat: uri_dbpedia},
        unmatched_istat lista dei codici ISTAT non risolti.
    """
    overrides = manual_overrides if manual_overrides is not None else DBPEDIA_MANUAL_OVERRIDES

    # Index DBpedia: nome "core" (post-strip prefisso) → URI.
    # Indicizziamo entrambe le forme con/senza "e/and" per matching cross-lingua.
    dbpedia_by_norm: dict[str, str] = {}
    for row in dbpedia_rows:
        for label_field in ("label_it", "label_en"):
            label = row.get(label_field, "")
            if not label:
                continue
            norm = _normalize_province_name(label)
            core = _strip_dbpedia_prefix(norm)
            for form in _equivalent_forms(core):
                dbpedia_by_norm.setdefault(form, row["resource"])

    mapping: dict[str, str] = {}
    unmatched: list[str] = []
    for codice_istat, meta in agid_provinces.items():
        # 1. Manual override (priorità massima)
        if codice_istat in overrides:
            mapping[codice_istat] = overrides[codice_istat]
            continue
        # 2. Match esatto su prefLabel normalizzato (con varianti e/and)
        norm = _normalize_province_name(meta["prefLabel"])
        found = False
        for form in _equivalent_forms(norm):
            if form in dbpedia_by_norm:
                mapping[codice_istat] = dbpedia_by_norm[form]
                found = True
                break
        if found:
            continue
        # 3. Unmatched: il chiamante decide il fallback
        unmatched.append(codice_istat)

    return mapping, unmatched


def emit_agid_to_dbpedia_sidecar(
    mapping: dict[str, str],
    output_path: Path,
    source_endpoint: str = DBPEDIA_SPARQL_ENDPOINT,
) -> None:
    """Materializza il sidecar TTL con N triple owl:sameAs + header prov:Entity."""
    from rdflib import Graph, Literal, Namespace, URIRef
    from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

    idpt = Namespace("https://example.org/idpt/")
    agidp = Namespace(
        "https://w3id.org/italia/controlled-vocabulary/"
        "territorial-classifications/provinces/"
    )

    g = Graph()
    g.bind("agidp", agidp)
    g.bind("owl", OWL)
    g.bind("dcterms", DCTERMS)
    g.bind("rdfs", RDFS)

    # Header prov:Entity
    sidecar_uri = idpt["agid-to-dbpedia-graph"]
    g.add((sidecar_uri, RDF.type, DCTERMS.Standard))
    g.add((sidecar_uri, DCTERMS.title, Literal(
        "Sidecar linking province AGID → DBpedia", lang="it")))
    g.add((sidecar_uri, DCTERMS.description, Literal(
        f"{len(mapping)} triple owl:sameAs fra province AGID e risorse DBpedia, "
        "ottenute via query SPARQL su https://dbpedia.org/sparql + reconciliation "
        "manuale per anomalie nominali (Reggio C/E, città metropolitane, PA, "
        "Sud Sardegna, BAT/Fermo/Monza-Brianza).", lang="it")))
    g.add((sidecar_uri, DCTERMS.created, Literal(
        datetime.date.today().isoformat(), datatype=XSD.date)))
    g.add((sidecar_uri, DCTERMS.source, URIRef(source_endpoint)))
    g.add((sidecar_uri, DCTERMS.license, URIRef(
        "https://creativecommons.org/licenses/by/4.0/")))

    # Le N triple owl:sameAs
    for codice_istat, uri_dbpedia in mapping.items():
        prov_uri = URIRef(str(agidp) + codice_istat)
        g.add((prov_uri, OWL.sameAs, URIRef(uri_dbpedia)))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(output_path), format="turtle")


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provinces-ttl", type=Path, required=True,
        help="Path al TTL AGID delle province (data/provinces.ttl)."
    )
    parser.add_argument(
        "--out-ttl", type=Path, required=True,
        help="Path del sidecar TTL da generare (output/mappings/agid_to_dbpedia.ttl)."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Non scrivere il file, stampa solo lo stato del match."
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Esce con errore non-zero se non si raggiunge 107/107 match."
    )
    args = parser.parse_args()

    print(f"=== generate_agid_to_dbpedia ===")
    print(f"Endpoint: {DBPEDIA_SPARQL_ENDPOINT}")
    print(f"AGID TTL: {args.provinces_ttl}")
    print(f"Output:   {args.out_ttl}{' (DRY RUN)' if args.dry_run else ''}")
    print()

    agid = load_agid_provinces(args.provinces_ttl)
    print(f"✓ AGID: {len(agid)} province caricate")

    print("→ Query DBpedia (può richiedere 5-30 sec)...")
    try:
        dbpedia_rows = query_dbpedia_italian_provinces()
    except Exception as e:
        print(f"✗ Query DBpedia fallita: {type(e).__name__}: {e}")
        return 1
    print(f"✓ DBpedia: {len(dbpedia_rows)} risorse province/metropolitan-city italiane")

    mapping, unmatched = reconcile_dbpedia_to_agid(dbpedia_rows, agid)
    print(f"✓ Riconciliati: {len(mapping)}/107")
    if unmatched:
        print(f"⚠ Non risolti ({len(unmatched)}):")
        for code in unmatched:
            print(f"    {code}  {agid[code]['prefLabel']}")
        print()
        print("→ Aggiungi override manuali a DBPEDIA_MANUAL_OVERRIDES nel codice")
        print("  e rilancia lo script per chiudere i casi residui.")

    if args.strict and unmatched:
        print(f"\n✗ Strict mode: {len(unmatched)} unmatched. Exit 1.")
        return 1

    if not args.dry_run:
        emit_agid_to_dbpedia_sidecar(mapping, args.out_ttl)
        print(f"\n✓ Sidecar scritto: {args.out_ttl} ({len(mapping)} triple owl:sameAs)")
    else:
        print("\n(dry-run, niente file scritto)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
