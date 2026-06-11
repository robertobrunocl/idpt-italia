"""MCP server per interrogare il grafo Atlante IDPT da Claude Desktop.

Questo modulo espone il grafo RDF dell'Atlante IDPT come server MCP (Model
Context Protocol) che Claude Desktop può utilizzare. Permette di interrogare
il grafo in linguaggio naturale: Claude traduce la richiesta in SPARQL, la
esegue contro l'endpoint Fuseki locale e formatta la risposta in italiano.

Setup completo:

  1. Avvia Fuseki e carica il grafo (in un terminale dedicato):

         bash scripts/start_fuseki.sh
         bash scripts/load_fuseki.sh

  2. Installa le dipendenze del server MCP:

         pip install mcp SPARQLWrapper

  3. Configura Claude Desktop. Su macOS apri il file:

         ~/Library/Application Support/Claude/claude_desktop_config.json

     e aggiungi (sostituendo il path con quello reale del progetto):

         {
           "mcpServers": {
             "idpt-graph": {
               "command": "python3",
               "args": [
                 "/path/assoluto/al/progetto/scripts/mcp_idpt_server.py"
               ]
             }
           }
         }

  4. Riavvia Claude Desktop. Il tool `sparql_query` diventerà disponibile e
     si attiverà automaticamente quando farai una domanda interpretabile sul
     grafo IDPT.

Esempi di domande in linguaggio naturale che Claude può rispondere:

  • "Quali sono le 5 province italiane con IDPT più alto?"
  • "Qual è il valore IDPT di Palermo e come si scompone nelle tre componenti?"
  • "Confronta il monte pensioni di Milano e Napoli in mld di euro."
  • "Quante pensioni in regime retributivo ci sono in Lombardia?"
  • "Quali sono i territori dove c'è meno divario fra speranza di vita
     a 65 anni e età media alla decorrenza pensionistica?"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    sys.stderr.write(
        "ERRORE: il pacchetto 'mcp' non è installato.\n"
        "Esegui: pip install mcp SPARQLWrapper\n"
    )
    sys.exit(1)

try:
    from SPARQLWrapper import SPARQLWrapper, JSON as SPARQL_JSON
except ImportError:
    sys.stderr.write(
        "ERRORE: il pacchetto 'SPARQLWrapper' non è installato.\n"
        "Esegui: pip install SPARQLWrapper\n"
    )
    sys.exit(1)

# Endpoint SPARQL Fuseki — modifica se necessario.
SPARQL_ENDPOINT = "http://localhost:3030/idpt/sparql"

# Path al file ontologia (per esporlo come risorsa MCP).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ONTOLOGY_PATH = PROJECT_ROOT / "output" / "vocabularies" / "ontology.ttl"

mcp = FastMCP("idpt-graph")


@mcp.tool()
def sparql_query(query: str) -> str:
    """Esegue una query SPARQL sul grafo Atlante IDPT e ritorna i risultati.

    Il grafo contiene ~117.000 triple distribuite in 6 grafi nominati Fuseki:

      - graph:vocabularies: ontologia (1 owl:Class propria idpt:SedeINPS,
        9 qb:DataStructureDefinition, 6 skos:ConceptScheme con 27 Concept,
        10 qb:DimensionProperty, 9 qb:MeasureProperty)
      - graph:observations: 8 cubi statistici primari (12.884 qb:Observation)
      - graph:idpt-computed: il cubo 8 con l'IDPT (428 qb:Observation,
        107 province × 3 componenti + 1 aggregato, tutte obsStatus=E)
      - graph:linking: 3 sidecar di interlinking (107 owl:sameAs verso DBpedia,
        106 idpt:SedeINPS, alias NUTS)
      - graph:metadata: il dcatapit:Dataset del deliverable
      - graph:agid: vocabolari controllati territoriali AGID OntoPiA
        (107 clv:Province + 20 clv:Region, read-only)

    PREFISSI utili (puoi dichiararli esplicitamente nella query):

      PREFIX idpt:    <https://robertobrunocl.github.io/idpt-italia/>
      PREFIX qb:      <http://purl.org/linked-data/cube#>
      PREFIX skos:    <http://www.w3.org/2004/02/skos/core#>
      PREFIX clv:     <https://w3id.org/italia/onto/CLV/>
      PREFIX agidp:   <https://w3id.org/italia/controlled-vocabulary/territorial-classifications/provinces/>
      PREFIX agidr:   <https://w3id.org/italia/controlled-vocabulary/territorial-classifications/regions/>
      PREFIX sdmx-attribute: <http://purl.org/linked-data/sdmx/2009/attribute#>
      PREFIX sdmx-code:      <http://purl.org/linked-data/sdmx/2009/code#>
      PREFIX prov:    <http://www.w3.org/ns/prov#>
      PREFIX owl:     <http://www.w3.org/2002/07/owl#>
      PREFIX xsd:     <http://www.w3.org/2001/XMLSchema#>

    CONCETTI CHIAVE del dominio:

      Cubi (qb:DataSet) — passali come oggetto di `qb:dataSet`:
        idpt:cubo-pensioni-vigenti-residenza      (cubo 1, dimensione D1 + D2)
        idpt:cubo-pensioni-regime-sede            (cubo 2, dimensione D3)
        idpt:cubo-pensioni-serie-storica-sede     (cubo 3, serie 1998-2026)
        idpt:cubo-pensioni-decorrenza-gdp         (cubo 4, decorrenza GDP)
        idpt:cubo-occupati-istat                  (cubo 5, denominatore D1)
        idpt:cubo-indicatori-demografici-istat    (cubo 6, contesto)
        idpt:cubo-redditi-mef                     (cubo 7, denominatore D2)
        idpt:cubo-idpt-computed                   (cubo 8, IDPT calcolato)
        idpt:cubo-plan-b-gdp-projected            (cubo 9, Plan B GDP)

      Componenti IDPT — usali come oggetto di `idpt:componenteIDPT`:
        idpt:componente-pressione-demografica     (D1)
        idpt:componente-peso-economico            (D2)
        idpt:componente-eredita-storica           (D3)
        idpt:idpt-aggregato                       (valore IDPT finale)

      Gestioni INPS — `idpt:tipoGestione`:
        idpt:gestione-privati, idpt:gestione-pubblici,
        idpt:gestione-autonomi-parasub, idpt:gestione-assistenziali,
        idpt:gestione-totale

      Regimi liquidazione — `idpt:regimeLiquidazione`:
        idpt:regime-retributivo, idpt:regime-misto-dini,
        idpt:regime-misto-fornero, idpt:regime-contributivo-puro

      Indicatori demografici — `idpt:indicatoreDemografico`:
        idpt:ind-pop014, idpt:ind-pop1564, idpt:ind-pop65over,
        idpt:ind-oldagedepr, idpt:ind-ageindex, idpt:ind-meanagep,
        idpt:ind-birthrate, idpt:ind-lifeexp65t

      Voci reddito MEF — `idpt:voceReddito`:
        idpt:voce-redd-lavoro-dipendente (v2), idpt:voce-redd-lavoro-autonomo (v4),
        idpt:voce-redd-imprenditore-ord (v5), idpt:voce-redd-imprenditore-sempl (v6),
        idpt:voce-redd-partecipazione (v7)

    PATTERN comuni:

      - Filtrare la lingua delle label: `FILTER(LANG(?label) = "it")`
      - Province di una regione: `?p clv:situatedWithin agidr:<NN>`
        (es. agidr:18 = Calabria, agidr:03 = Lombardia, agidr:15 = Campania)
      - Osservazioni stimate: `sdmx-attribute:obsStatus sdmx-code:obsStatus-E`
      - Catena di derivazione: `?obs prov:wasDerivedFrom+ ?origine`

    Args:
        query: La query SPARQL completa (con PREFIX dichiarati).

    Returns:
        I risultati della query in formato JSON SPARQL standard, oppure un
        messaggio di errore se la query fallisce o Fuseki è irraggiungibile.
    """
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(SPARQL_JSON)
    sparql.setTimeout(30)  # secondi
    try:
        result = sparql.query().convert()
        # Compatta il JSON: tieni le variabili e i binding ma rimuovi
        # rumore (datatype URI, xml:lang quando non serve).
        if "results" in result and "bindings" in result["results"]:
            rows = result["results"]["bindings"]
            vars_ = result.get("head", {}).get("vars", [])
            simple = [
                {v: b[v].get("value", "") for v in vars_ if v in b}
                for b in rows
            ]
            return json.dumps(
                {
                    "columns": vars_,
                    "rows": simple,
                    "row_count": len(simple),
                },
                ensure_ascii=False,
                indent=2,
            )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as exc:
        msg = str(exc)
        if "Connection refused" in msg or "Could not connect" in msg.lower():
            return (
                f"ERRORE: impossibile raggiungere Fuseki a {SPARQL_ENDPOINT}. "
                f"Assicurati di averlo avviato con `bash scripts/start_fuseki.sh` "
                f"e di aver caricato il grafo con `bash scripts/load_fuseki.sh`."
            )
        return f"ERRORE durante l'esecuzione della query SPARQL: {msg}"


@mcp.tool()
def graph_summary() -> str:
    """Restituisce un riassunto dei contenuti principali del grafo IDPT.

    Utile come prima chiamata per orientarsi: conta le triple totali, i
    qb:DataSet, le qb:Observation, le owl:Class, le code-list SKOS.
    """
    counts_query = """
    PREFIX qb:   <http://purl.org/linked-data/cube#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX owl:  <http://www.w3.org/2002/07/owl#>
    SELECT
      (COUNT(DISTINCT ?cubo) AS ?n_cubi)
      (COUNT(DISTINCT ?obs)  AS ?n_obs)
      (COUNT(DISTINCT ?cs)   AS ?n_concept_scheme)
      (COUNT(DISTINCT ?c)    AS ?n_concept)
    WHERE {
      { ?cubo a qb:DataSet }
      UNION
      { ?obs a qb:Observation }
      UNION
      { ?cs a skos:ConceptScheme }
      UNION
      { ?c a skos:Concept }
    }
    """
    return sparql_query(counts_query)


@mcp.resource("idpt://ontology")
def get_ontology() -> str:
    """L'ontologia formale del progetto IDPT, in formato Turtle.

    Contiene la dichiarazione owl:Ontology con metadati, la classe propria
    idpt:SedeINPS, le 10 qb:DimensionProperty e le 9 qb:MeasureProperty con
    rdfs:domain qb:Observation, le 9 qb:DataStructureDefinition (una per
    cubo) e le 6 skos:ConceptScheme. Totale: 570 triple.
    """
    if ONTOLOGY_PATH.exists():
        return ONTOLOGY_PATH.read_text(encoding="utf-8")
    return f"ERRORE: ontologia non trovata a {ONTOLOGY_PATH}"


@mcp.resource("idpt://schema-description")
def get_schema_description() -> str:
    """Descrizione narrativa dello schema del grafo IDPT.

    Riferimento rapido per chi vuole un orientamento prima di scrivere
    query SPARQL: spiega i 9 cubi, le loro dimensioni e misure principali,
    le code-list, le ancore territoriali.
    """
    return """\
Schema del grafo IDPT (Atlante della dipendenza previdenziale italiana)
======================================================================

Provenance: 9 dataset CSV (4 INPS Osservatorio Statistico, 3 ISTAT, 1 MEF,
1 GeoJSON Openpolis) + 2 vocabolari controllati AGID OntoPiA, processati con
la libreria macrorefine e materializzati come grafo RDF.

I 9 cubi qb:DataSet (totale 13.312 qb:Observation):

  1. cubo-pensioni-vigenti-residenza
     Dim: idpt:provincia × idpt:annoRiferimento × idpt:tipoGestione
     Misure: idpt:numeroPensioni, idpt:importoMedioMensile,
             idpt:importoAnnuoComplessivo
     535 obs. Numeratore della componente D1 e D2 dell'IDPT.

  2. cubo-pensioni-regime-sede (stile B con qb:measureType)
     Dim: idpt:sedeINPS × idpt:annoRiferimento × idpt:regimeLiquidazione
          × qb:measureType
     Misure: come sopra ma una obs = una misura
     1.272 obs. Dimensione D3 dell'IDPT (eredità storica).

  3. cubo-pensioni-serie-storica-sede (stile B)
     Dim: idpt:sedeINPS × idpt:annoRiferimento (29 anni 1998-2026) ×
          idpt:tipoGestione × qb:measureType
     9.105 obs. Prospettiva diacronica.

  4. cubo-pensioni-decorrenza-gdp
     Dim: idpt:areaGeografica × idpt:annoDecorrenza
     Misure: idpt:numeroPensioni, idpt:etaMediaDecorrenza, ...
     46 obs. Decorrenza GDP nazionale.

  5. cubo-occupati-istat
     Dim: idpt:provincia × idpt:annoRiferimento
     Misura: idpt:numeroOccupati
     107 obs. Denominatore D1 (occupati).

  6. cubo-indicatori-demografici-istat
     Dim: idpt:provincia × idpt:annoRiferimento × idpt:indicatoreDemografico
     Misura: idpt:valoreIndicatore
     856 obs. Variabili di contesto.

  7. cubo-redditi-mef
     Dim: idpt:provincia × idpt:annoRiferimento × idpt:voceReddito
     Misure: idpt:frequenzaDichiaranti, idpt:ammontareTotale
     535 obs. Denominatore D2 (monte redditi).

  8. cubo-idpt-computed
     Dim: idpt:provincia × idpt:annoRiferimento × idpt:componenteIDPT
     Misura: idpt:valoreIDPT (xsd:decimal in [0,1])
     428 obs (107 province × 4 concetti). L'IDPT calcolato, materializzato.
     Tutte obsStatus=E + prov:wasDerivedFrom verso cubi primari.

  9. cubo-plan-b-gdp-projected
     Dim: idpt:provincia × idpt:annoRiferimento × idpt:regimeLiquidazione
     Misura: idpt:numeroPensioni
     428 obs (107 × 4 regimi). Plan B: proiezione composizione regime
     pubblici dal cubo 4 nazionale.

Le province italiane sono identificate con le URI canoniche AGID OntoPiA
(prefisso agidp:), es. agidp:001 = Torino, agidp:082 = Palermo. Ogni
provincia è collegata a NUTS Eurostat (owl:sameAs nativi) e a DBpedia
(107 owl:sameAs materializzati nel sidecar agid_to_dbpedia.ttl).

Componenti dell'IDPT (codici skos:Concept di idpt:componenti-idpt):
  - idpt:componente-pressione-demografica  (D1, pensioni vigenti / occupati)
  - idpt:componente-peso-economico         (D2, monte pensioni / monte redditi)
  - idpt:componente-eredita-storica        (D3, % retributivo)
  - idpt:idpt-aggregato                    (media aritmetica D1+D2+D3 normalizzati)
"""


if __name__ == "__main__":
    mcp.run()
