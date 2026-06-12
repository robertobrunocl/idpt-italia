# Atlante della dipendenza previdenziale italiana — IDPT 2026

> Una prospettiva storico-territoriale sulla sostenibilità del sistema
> pensionistico italiano, realizzata aggregando 9 dataset pubblici di basso
> livello (CSV INPS, ISTAT, MEF) + 2 vocabolari controllati AGID e portandoli
> a **Linked Open Data 5★**.

## In una riga

Costruzione, materializzazione e pubblicazione di un grafo RDF di
**~120.000 triple** (di cui ~117.000 prodotte dal progetto, più il vocabolario AGID riusato) che modella la dipendenza previdenziale di tutte le 107
province italiane al 1.1.2026 attraverso l'**Indice di Dipendenza
Previdenziale Territoriale (IDPT)**, un indice composito di 3 componenti
(pressione demografica, peso economico, eredità storica delle riforme).

## Il deliverable

Il grafo RDF finale contiene **13.312 `qb:Observation`** distribuite su
**9 `qb:DataSet`** modellati con RDF Data Cube, ancorate alle URI canoniche
AGID delle 107 province e linkate esternamente a DBpedia tramite 107
asserzioni `owl:sameAs`. I file Turtle principali sono:

- **`output/computed/cubo8_idpt_computed.ttl`** — IDPT materializzato come
  `qb:Observation` con `prov:wasDerivedFrom` esplicito (428 obs)
- **`output/observations/cubo[1-7,9].ttl`** — 8 cubi `qb:DataSet` primari
  (12.884 obs totali)
- **`output/dataset/atlante_idpt_dataset.ttl`** — `dcatapit:Dataset` con
  metadati completi (DCAT-AP_IT)
- **`output/visualizations/idpt_map.html`** — mappa coropletica interattiva
- **`output/vocabularies/`** — 6 code-list SKOS + 9 DSD qb + classe propria
  `idpt:SedeINPS` (file `classes_and_properties.ttl` e `code_lists.ttl`) +
  **`ontology.ttl`** (bundle aggregato per Protégé)
- **`output/mappings/`** — 3 sidecar di linking (NUTS aliases, INPS↔AGID,
  AGID→DBpedia)

## Top 5 IDPT (province più "dipendenti" dal sistema pensionistico)

| # | Provincia | IDPT |
|---|---|---:|
| 1 | Reggio di Calabria | **0.675** |
| 2 | Taranto | 0.651 |
| 3 | Catanzaro | 0.627 |
| 4 | Oristano | 0.580 |
| 5 | Nuoro | 0.552 |

## Bottom 5 (meno dipendenti)

| # | Provincia | IDPT |
|---|---|---:|
| 103 | Padova | 0.141 |
| 104 | Prato | 0.121 |
| 105 | Trento | 0.104 |
| 106 | Milano | 0.100 |
| 107 | Bolzano | **0.034** |

Divario Nord/Sud netto, con un rapporto di circa 20× fra le province più
dipendenti e quelle meno dipendenti.

## Prerequisiti

- **Python** ≥ 3.10 (testato su 3.11)
- **Java** ≥ 17 LTS (raccomandato Eclipse Temurin 21, per Apache Jena Fuseki 5.x)
- **bash** (gli script di setup sono shell script POSIX)
- **Sistema operativo**: testato su macOS e Linux. Su Windows usare WSL2.
- Connessione di rete necessaria solo per: download iniziale di Fuseki
  (`scripts/setup.sh`) e generazione del sidecar DBpedia
  (`scripts/generate_agid_to_dbpedia.py`). La pipeline è altrimenti offline.

## Setup end-to-end

```bash
# 1. Ambiente Python + Java + scarico Fuseki locale
bash scripts/setup.sh

# 2. Test ancora semantica AGID (smoke test)
python scripts/smoke_test_agid.py

# 3. Avvia Fuseki (in un terminale, lascia girare in background)
bash scripts/start_fuseki.sh
# IMPORTANTE: lo script avvia Fuseki con --set tdb:unionDefaultGraph=true,
# necessario per interrogare correttamente i grafi nominati (vedi sez. 5.2
# del REPORT.md).

# 4. Esegui le 9 Recipe in ordine
python scripts/recipes/cubo5_occupati_istat.py            # 107 obs
python scripts/recipes/cubo7_redditi_mef.py               # 535 obs
python scripts/recipes/cubo6_indicatori_demografici_istat.py  # 856 obs
python scripts/recipes/cubo1_vigenti_residenza.py         # 535 obs
python scripts/recipes/cubo4_decorrenza_gdp.py            # 46 obs
python scripts/recipes/cubo9_plan_b_gdp_projected.py      # 428 obs
python scripts/recipes/cubo2_regime_sede.py               # 1.272 obs
python scripts/recipes/cubo3_serie_storica_sede.py        # 9.105 obs
python scripts/recipes/cubo8_idpt_computed.py             # 428 obs (IDPT!)

# 5. Validation a 3 livelli
python scripts/validate_vocabularies.py     # 10/10 check SPARQL
python scripts/validate_observations.py     # 9/9 check SPARQL
python scripts/validate_dataset.py          # 14/14 check SPARQL

# 6. Carica i 6 grafi nominati in Fuseki + esegui le 12 query SPARQL di demo
bash scripts/load_fuseki.sh
bash scripts/run_sparql_demo.sh

# 7. Genera mappe coropletiche
python scripts/build_maps.py
```

## Esplorare l'ontologia con Protégé

Il file **`output/vocabularies/ontology.ttl`** è un bundle aggregato dei due
file ontologici del progetto (`classes_and_properties.ttl` +
`code_lists.ttl`) con header `owl:Ontology` e metadati ricchi (titolo,
descrizione, creator, publisher, licenza, versione). Si apre direttamente
in [Protégé](https://protege.stanford.edu/) via *File → Open File*, e
mostra ad albero:

- 1 `owl:Class` propria (`idpt:SedeINPS`, sottoclasse di `clv:Feature`)
- 2 `owl:ObjectProperty` proprie
- 10 `qb:DimensionProperty` e 9 `qb:MeasureProperty`
- 9 `qb:DataStructureDefinition` (una per cubo)
- 6 `skos:ConceptScheme` con 27 `skos:Concept` totali

I due file sorgente restano la fonte di verità per il caricamento nei
grafi nominati Fuseki.

## Interrogare il grafo via SPARQL

Le 12 query di demo sono in `scripts/sparql/q01_*.rq` ... `q12_*.rq`,
eseguibili individualmente o in batch via `bash scripts/run_sparql_demo.sh`.
Coprono dalla classifica IDPT al drill-down per provincia, dall'evoluzione
storica del numero di pensioni in 28 anni alla durata attesa di una
pensione provincia per provincia. La trattazione completa con snippet e
risultati attesi è nella sez. 5.2 del `REPORT.md`.

## Struttura repository

```
.
├── REPORT.md                         # report del progetto
├── README.md                         # questo file
├── data/                             # CSV grezzi + TTL AGID (read-only)
│   ├── inps_*.csv                    # 5 dataset INPS (4 attivi + 1 ispezione)
│   ├── istat_*.csv                   # 3 dataset ISTAT
│   ├── mef_*.csv                     # 1 dataset MEF
│   ├── provinces.ttl + regions.ttl   # vocabolari AGID OntoPiA
│   └── limits_IT_provinces.geojson   # geometrie province (Openpolis)
├── output/                           # grafo RDF prodotto
│   ├── vocabularies/                 # SKOS code-list + DSD qb + classi
│   │   ├── classes_and_properties.ttl
│   │   ├── code_lists.ttl
│   │   └── ontology.ttl              # bundle aggregato per Protégé
│   ├── observations/                 # 8 cubi qb:DataSet primari
│   ├── computed/                     # cubo 8 IDPT computed
│   ├── mappings/                     # 3 sidecar di linking
│   ├── dataset/                      # DCAT-AP_IT deliverable
│   ├── dist/                         # 3 distribuzioni (TTL/JSON-LD/ZIP)
│   └── visualizations/               # mappe Folium HTML
├── docs/                             # landing page GitHub Pages
├── scripts/                          # 9 Recipe + 6 script + 12 query SPARQL
│   ├── recipes/                      # le 9 Recipe macrorefine
│   └── sparql/                       # le 12 query .rq di demo
└── macrorefine/                      # libreria di data cleaning (editable install)
```

## Caratteristiche LOD del grafo

- **9 vocabolari standard riusati**: qb, SKOS, CLV OntoPiA, sdmx-attribute,
  OWL-Time, DCAT-AP_IT, owl:sameAs, prov:wasDerivedFrom, foaf/vcard
- **1 sola classe propria** (`idpt:SedeINPS`); tutto il resto sono istanze
  di classi standard
- **9 `qb:DataSet`** modellati come Data Cube W3C (un cubo per fenomeno)
- **6 code-list SKOS** (tipi gestione INPS, regimi liquidazione, indicatori
  demografici, voci reddito MEF, componenti IDPT, aree geografiche)
- **Linking esterno**: 107 `owl:sameAs` verso DBpedia (quintupla identità
  AGID + NUTS + DBpedia + altLabel INPS + sede INPS per ogni provincia)
- **Pattern "osservazione derivata"** uniforme in 4 punti (4.399 obs stimate
  totali con `obsStatus=E` + `prov:wasDerivedFrom`): aggregazione storica
  Sardegna 2005–2011, importo annuo ricostruito sui cubi 2 e 3, Plan B GDP,
  IDPT computed
- **Stile mix qb**: stile A (multi-measure) per cubi 1+4+5+6+7+8+9, stile B
  (`qb:measureType`) per cubi 2+3
- **DCAT-AP_IT** per metadati conformi al profilo italiano AGID

## Interrogazione in linguaggio naturale via MCP (opzionale)

Il grafo IDPT può essere interrogato in **linguaggio naturale** da Claude
Desktop o da qualunque altro client che supporta il [Model Context Protocol
(MCP)](https://modelcontextprotocol.io/). Lo script
`scripts/mcp_idpt_server.py` espone il grafo come server MCP: Claude traduce
la domanda in italiano in SPARQL, la esegue contro il Fuseki locale e
formatta la risposta.

Esempi di domande possibili:

- *"Quali sono le 5 province italiane con IDPT più alto?"*
- *"Qual è il valore IDPT di Palermo e come si scompone nelle tre componenti?"*
- *"Confronta il monte pensioni di Milano e Napoli in mld di euro."*

Setup:

```bash
# 1. Avvia Fuseki (in un terminale dedicato) + carica il grafo
bash scripts/start_fuseki.sh
bash scripts/load_fuseki.sh

# 2. Installa le dipendenze MCP (già in requirements.txt come opzionali)
pip install mcp SPARQLWrapper

# 3. Configura Claude Desktop. Su macOS apri il file
#    ~/Library/Application Support/Claude/claude_desktop_config.json
#    e aggiungi (sostituendo il path con quello reale del progetto):
```

```json
{
  "mcpServers": {
    "idpt-graph": {
      "command": "python3",
      "args": ["/path/assoluto/al/progetto/scripts/mcp_idpt_server.py"]
    }
  }
}
```

Riavvia Claude Desktop. Il tool `sparql_query` diventa disponibile e si
attiva automaticamente quando la conversazione lo richiede. Lo script
espone anche `graph_summary()` (riassunto rapido del grafo) e due risorse
MCP: l'ontologia in Turtle e una descrizione narrativa dello schema dei
9 cubi.

## Deploy GitHub Pages (per chi clona il repo)

Il progetto è già deployato su <https://robertobrunocl.github.io/idpt-italia/>.
La sezione che segue spiega **come pubblicare una propria copia del progetto
sotto un account GitHub diverso**, per riproducibilità e riuso. Non è
necessaria per consultare il deliverable corrente.

Per pubblicare il grafo come sito statico GitHub Pages con namespace
risolvibile via HTTP:

```bash
# Sostituisce il namespace placeholder con quello finale GitHub Pages
# (find-and-replace globale su tutti i file TTL del progetto)
python scripts/finalize_namespace.py --username YOURNAME

# Push del repository, poi abilitazione GitHub Pages
# Settings → Pages → Source: main branch, /docs/ folder
git add -A && git commit -m "Finalize namespace + deploy"
git push origin main
```

La landing page sarà disponibile a
`https://YOURNAME.github.io/idpt-italia/`.

## Documentazione

Il documento principale del progetto è **`REPORT.md`** in questa directory:
abstract, dataset di partenza con link e licenze, elaborazione con
macrorefine, trasformazione RDF + ontologia, visualizzazione e query
SPARQL, licenza del deliverable.

## Licenza

Il grafo RDF dell'Atlante IDPT è rilasciato sotto licenza **CC-BY 4.0**.
La scelta è compatibile con tutte e cinque le licenze sorgente:

| Fonte | Licenza |
|---|---|
| INPS — Osservatorio statistico | IODL 2.0 |
| ISTAT — `esploradati.istat.it` | CC-BY 3.0 IT |
| MEF — Dip. Finanze | CC-BY 3.0 |
| AGID — OntoPiA | CC-BY 4.0 |
| Openpolis (eredità ISTAT) | CC-BY |

DBpedia (CC-BY-SA 3.0) è target del linking esterno via `owl:sameAs` ma
non viene duplicato nel deliverable, quindi la clausola share-alike non
si propaga. Dettagli sulla compatibilità in `REPORT.md` sez. 6.

## Autore

Roberto Bruno — anno accademico 2025/2026.
