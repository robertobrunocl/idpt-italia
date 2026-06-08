"""scripts/smoke_test_agid.py — Smoke test dell'ancora semantica AGID.

Verifica che il vocabolario controllato delle province AGID (`data/provinces.ttl`)
sia caricabile, interrogabile via SPARQL, e contenga esattamente le 107 province
attese, ciascuna ben formata.

Eseguito una volta in Fase 0 (setup) e ripetibile come regression test prima di
ogni esecuzione della pipeline. Se uno degli `assert` qui fallisce, ci si ferma:
le 107 URI AGID sono il punto fisso semantico del progetto.

Scoperta documentata durante Fase 0: il TTL AGID preserva i codici NUTS storici
come `owl:sameAs` multipli (revisioni NUTS-3 nel tempo). 6 province italiane
hanno più di un NUTS associato — la più articolata è Sud Sardegna (5 NUTS, è
nata nel 2016 da molte revisioni). Le query del progetto vanno sempre scritte
con questo in mente: niente OPTIONAL ingenue su NUTS che producono prodotto
cartesiano implicito.

Uso:
    source .venv/bin/activate
    python scripts/smoke_test_agid.py
"""

from __future__ import annotations

from pathlib import Path

from rdflib import Graph

# -----------------------------------------------------------------------------
# Configurazione
# -----------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROVINCES_TTL = PROJECT_ROOT / "data" / "provinces.ttl"

# Costanti attese (decisioni metodologiche, sez. 4 + 10.9 di PROGETTO_CONTESTO.md)
EXPECTED_TOTAL_PROVINCES = 107
EXPECTED_METRO_CITIES = 14  # clv:hasRankOrder = "4"
EXPECTED_ORDINARY_PROVINCES = 93  # clv:hasRankOrder = "3"

# Scoperta della Fase 0: 6 province con NUTS multipli (revisioni storiche)
EXPECTED_PROVINCES_WITH_MULTI_NUTS = 6
EXPECTED_TOTAL_NUTS_LINKS = 116  # 107 + 9 NUTS storici extra
PROVINCES_WITH_MULTI_NUTS = {
    "016": ("Bergamo", 2),
    "030": ("Udine", 2),
    "090": ("Sassari", 2),
    "091": ("Nuoro", 2),
    "099": ("Rimini", 2),
    "111": ("Sud Sardegna", 5),
}

# -----------------------------------------------------------------------------
# Query SPARQL
# -----------------------------------------------------------------------------

# Query 1 — Le 107 province distinte, una riga per provincia.
# SELECT DISTINCT per evitare il prodotto cartesiano implicito con i NUTS
# multipli. NB: niente OPTIONAL su NUTS qui — gestito separatamente in Q2.
QUERY_PROVINCES = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX clv:  <https://w3id.org/italia/onto/CLV/>

SELECT DISTINCT ?prov ?prefLabel ?codiceIstat ?sigla ?regione
WHERE {
  ?prov a clv:Province ;
        skos:prefLabel ?prefLabel ;
        skos:notation  ?codiceIstat ;
        clv:acronym    ?sigla ;
        clv:situatedWithin ?regione .
  FILTER(LANG(?prefLabel) = "it")
}
ORDER BY ?codiceIstat
"""

# Query 2 — Per ogni provincia, lista dei NUTS associati via owl:sameAs.
# Usa GROUP_CONCAT per aggregare 1..N NUTS in una stringa CSV per provincia.
# Restituisce sempre 107 righe; ?nNuts varia (1 nella maggioranza dei casi, 2-5
# per le province con revisioni storiche).
QUERY_NUTS_BY_PROVINCE = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX clv:  <https://w3id.org/italia/onto/CLV/>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>

SELECT ?codiceIstat
       (GROUP_CONCAT(DISTINCT STR(?nuts); SEPARATOR=",") AS ?nutsList)
       (COUNT(DISTINCT ?nuts) AS ?nNuts)
WHERE {
  ?prov a clv:Province ;
        skos:notation  ?codiceIstat .
  OPTIONAL {
    ?prov owl:sameAs ?nuts .
    FILTER(STRSTARTS(STR(?nuts), "http://nuts.geovocab.org/"))
  }
}
GROUP BY ?codiceIstat
ORDER BY ?codiceIstat
"""

# Query 3 — Città metropolitane vs province ordinarie via clv:hasRankOrder.
QUERY_RANK = """
PREFIX clv: <https://w3id.org/italia/onto/CLV/>

SELECT ?prov ?rank
WHERE {
  ?prov a clv:Province ;
        clv:hasRankOrder ?rank .
}
"""


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main() -> int:
    print("Smoke test AGID — provinces.ttl")
    print(f"File: {PROVINCES_TTL}")
    print()

    if not PROVINCES_TTL.exists():
        print(f"✗ File non trovato: {PROVINCES_TTL}")
        return 1

    # ---- 1. Carica il grafo ------------------------------------------------
    g = Graph()
    g.parse(str(PROVINCES_TTL), format="turtle")
    print(f"✓ Grafo caricato: {len(g):,} triple")

    # ---- 2. Q1: 107 province distinte ben formate --------------------------
    rows = list(g.query(QUERY_PROVINCES))
    assert len(rows) == EXPECTED_TOTAL_PROVINCES, (
        f"Atteso {EXPECTED_TOTAL_PROVINCES} province distinte, trovate {len(rows)}"
    )
    print(f"✓ {len(rows)}/{EXPECTED_TOTAL_PROVINCES} province AGID distinte (Q1)")

    # Verifiche per riga: tutte hanno sigla 2-char
    bad_sigla = [
        f"{istat} {label} → sigla={sigla!r}"
        for _prov, label, istat, sigla, _regione in rows
        if not sigla or len(str(sigla)) != 2
    ]
    assert not bad_sigla, f"Sigla malformata: {bad_sigla[:5]}"
    print(f"✓ {len(rows)}/{len(rows)} hanno sigla 2-char")

    # ---- 3. Q2: NUTS per provincia (gestione NUTS multipli storici) -------
    nuts_rows = list(g.query(QUERY_NUTS_BY_PROVINCE))
    assert len(nuts_rows) == EXPECTED_TOTAL_PROVINCES, (
        f"Q2: atteso {EXPECTED_TOTAL_PROVINCES} righe (una per provincia), "
        f"trovate {len(nuts_rows)}"
    )

    # Per ogni provincia, conteggio NUTS
    nuts_count_per_province = {
        str(istat): (int(n_nuts), str(nuts_list))
        for istat, nuts_list, n_nuts in nuts_rows
    }

    # Tutte le province devono avere ≥ 1 NUTS
    missing_nuts = [istat for istat, (n, _) in nuts_count_per_province.items() if n == 0]
    assert not missing_nuts, f"Province senza alcun NUTS: {missing_nuts}"
    print(f"✓ {len(rows)}/{len(rows)} hanno almeno 1 NUTS via owl:sameAs")

    # Totale NUTS = 116 (107 + 9 storici extra)
    total_nuts = sum(n for n, _ in nuts_count_per_province.values())
    assert total_nuts == EXPECTED_TOTAL_NUTS_LINKS, (
        f"Atteso {EXPECTED_TOTAL_NUTS_LINKS} NUTS totali (107 + 9 storici), "
        f"trovati {total_nuts}"
    )

    # Esattamente 6 province con NUTS multipli, con la cardinalità attesa
    multi_nuts = {
        istat: n for istat, (n, _) in nuts_count_per_province.items() if n > 1
    }
    assert len(multi_nuts) == EXPECTED_PROVINCES_WITH_MULTI_NUTS, (
        f"Atteso {EXPECTED_PROVINCES_WITH_MULTI_NUTS} province con NUTS multipli, "
        f"trovate {len(multi_nuts)}: {multi_nuts}"
    )
    for istat, (expected_label, expected_n) in PROVINCES_WITH_MULTI_NUTS.items():
        actual_n = multi_nuts.get(istat)
        assert actual_n == expected_n, (
            f"Provincia {istat} ({expected_label}): attesi {expected_n} NUTS, "
            f"trovati {actual_n}"
        )
    print(f"✓ {len(multi_nuts)} province con NUTS multipli, cardinalità corretta")
    print(f"  Totale NUTS owl:sameAs = {total_nuts} (= 107 + 9 storici)")

    # ---- 4. Q3: 14 città metropolitane (rank=4) + 93 ordinarie (rank=3) ---
    rank_rows = list(g.query(QUERY_RANK))
    rank_counts: dict[str, int] = {}
    for _prov, rank in rank_rows:
        rank_counts[str(rank)] = rank_counts.get(str(rank), 0) + 1

    metro = rank_counts.get("4", 0)
    ordinary = rank_counts.get("3", 0)
    assert metro == EXPECTED_METRO_CITIES, (
        f"Atteso {EXPECTED_METRO_CITIES} città metropolitane (rank=4), trovate {metro}"
    )
    assert ordinary == EXPECTED_ORDINARY_PROVINCES, (
        f"Atteso {EXPECTED_ORDINARY_PROVINCES} ordinarie (rank=3), trovate {ordinary}"
    )
    print(f"✓ {metro} città metropolitane (rank=4), {ordinary} ordinarie (rank=3)")

    # ---- 5. Sample per occhio umano ---------------------------------------
    print()
    print("Sample province (5 di interesse):")
    interesting_istat = {"001", "058", "092", "111", "085"}
    for prov, label, istat, sigla, regione in rows:
        if str(istat) in interesting_istat:
            regione_id = str(regione).rsplit("/", 1)[-1]
            n_nuts, nuts_list = nuts_count_per_province[str(istat)]
            nuts_short = ",".join(n.rsplit("/", 1)[-1] for n in nuts_list.split(","))
            print(
                f"  {istat}  {sigla}  {str(label):20s}  "
                f"NUTS[{n_nuts}]={nuts_short:25s} → regione {regione_id}"
            )

    print()
    print("Sample province con NUTS multipli:")
    for istat, (label_atteso, _n_atteso) in PROVINCES_WITH_MULTI_NUTS.items():
        n_nuts, nuts_list = nuts_count_per_province[istat]
        nuts_short = ",".join(n.rsplit("/", 1)[-1] for n in nuts_list.split(","))
        print(f"  {istat}  {label_atteso:18s}  NUTS[{n_nuts}]={nuts_short}")

    print()
    print("=== Smoke test AGID PASSATO ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
