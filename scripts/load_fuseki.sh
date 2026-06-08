#!/usr/bin/env bash
# scripts/load_fuseki.sh — Carica i TTL del progetto IDPT in Fuseki nei 6
# grafi nominati documentati in PROGETTO_CONTESTO.md sez. 10.16.
#
# Pre-requisito: Fuseki avviato in un altro terminale con:
#   bash scripts/start_fuseki.sh
#
# Strategia: HTTP POST su http://localhost:3030/idpt/data?graph=<URI> con
# Content-Type text/turtle. Idempotente: ogni esecuzione SOVRASCRIVE il
# contenuto del grafo (usa PUT) — utile per ricaricare dopo modifiche TTL.
#
# Uso:
#   bash scripts/load_fuseki.sh
#
# Variabili d'ambiente opzionali:
#   FUSEKI_ENDPOINT  default http://localhost:3030/idpt
#   PROJECT_ROOT     default cartella padre dello script

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

FUSEKI_ENDPOINT="${FUSEKI_ENDPOINT:-http://localhost:3030/idpt}"
DATA_URL="$FUSEKI_ENDPOINT/data"

echo "=== Carica grafi IDPT in Fuseki ==="
echo "Endpoint: $FUSEKI_ENDPOINT"
echo

# Verifica che Fuseki sia raggiungibile
if ! curl -fs "$FUSEKI_ENDPOINT/sparql?query=ASK%20WHERE%20%7B%20%3Fs%20%3Fp%20%3Fo%20%7D" >/dev/null 2>&1; then
  echo "⚠ Fuseki non raggiungibile su $FUSEKI_ENDPOINT"
  echo "  Avvialo con: bash scripts/start_fuseki.sh"
  exit 1
fi

# Funzione: carica un file TTL in un grafo nominato (PUT = sovrascrive)
load_graph() {
  local graph_uri="$1"
  local file_path="$2"
  if [[ ! -f "$file_path" ]]; then
    echo "  ⚠ file non trovato: $file_path"
    return 1
  fi
  local size_kb
  size_kb=$(du -k "$file_path" | cut -f1)
  printf "  Caricando %-50s (%5d KB) → %s\n" "$file_path" "$size_kb" "$graph_uri"
  # PUT: sovrascrive il contenuto del grafo
  curl -fsS -X PUT \
    -H "Content-Type: text/turtle" \
    --data-binary "@$file_path" \
    "${DATA_URL}?graph=$(printf %s "$graph_uri" | sed 's/:/%3A/g')" \
    >/dev/null
}

# Funzione: aggiunge un file a un grafo nominato esistente (POST = append)
append_to_graph() {
  local graph_uri="$1"
  local file_path="$2"
  if [[ ! -f "$file_path" ]]; then
    echo "  ⚠ file non trovato: $file_path"
    return 1
  fi
  local size_kb
  size_kb=$(du -k "$file_path" | cut -f1)
  printf "  Append %-54s (%5d KB) → %s\n" "$file_path" "$size_kb" "$graph_uri"
  curl -fsS -X POST \
    -H "Content-Type: text/turtle" \
    --data-binary "@$file_path" \
    "${DATA_URL}?graph=$(printf %s "$graph_uri" | sed 's/:/%3A/g')" \
    >/dev/null
}

# -----------------------------------------------------------------------------
# 1) graph:agid — vocabolario AGID OntoPiA (read-only, base territoriale)
# -----------------------------------------------------------------------------
echo "[1/6] graph:agid"
load_graph     "graph:agid" "data/provinces.ttl"
append_to_graph "graph:agid" "data/regions.ttl"

# -----------------------------------------------------------------------------
# 2) graph:vocabularies — classi + property + 9 DSD + 6 code-list
# -----------------------------------------------------------------------------
echo "[2/6] graph:vocabularies"
load_graph      "graph:vocabularies" "output/vocabularies/code_lists.ttl"
append_to_graph "graph:vocabularies" "output/vocabularies/classes_and_properties.ttl"

# -----------------------------------------------------------------------------
# 3) graph:linking — sidecar di riconciliazione
# -----------------------------------------------------------------------------
echo "[3/6] graph:linking"
load_graph      "graph:linking" "output/mappings/nuts_aliases.ttl"
append_to_graph "graph:linking" "output/mappings/inps_to_agid.ttl"
append_to_graph "graph:linking" "output/mappings/agid_to_dbpedia.ttl"

# -----------------------------------------------------------------------------
# 4) graph:observations — 8 cubi primari (1-7 + 9)
# -----------------------------------------------------------------------------
echo "[4/6] graph:observations"
load_graph      "graph:observations" "output/observations/cubo1_vigenti_residenza.ttl"
for ttl in cubo2_regime_sede cubo3_serie_storica_sede cubo4_decorrenza_gdp \
           cubo5_occupati_istat cubo6_indicatori_demografici_istat \
           cubo7_redditi_mef cubo9_plan_b_gdp_projected; do
  append_to_graph "graph:observations" "output/observations/${ttl}.ttl"
done

# -----------------------------------------------------------------------------
# 5) graph:idpt-computed — cubo 8 IDPT (grafo isolato per distribuzione DCAT)
# -----------------------------------------------------------------------------
echo "[5/6] graph:idpt-computed"
load_graph "graph:idpt-computed" "output/computed/cubo8_idpt_computed.ttl"

# -----------------------------------------------------------------------------
# 6) graph:metadata — DCAT-AP_IT deliverable
# -----------------------------------------------------------------------------
echo "[6/6] graph:metadata"
load_graph "graph:metadata" "output/dataset/atlante_idpt_dataset.ttl"

echo
echo "=== Caricamento completato ==="
echo
echo "Verifica via SPARQL:"
echo "  curl '$FUSEKI_ENDPOINT/sparql?query=SELECT+(COUNT(*)+AS+?n)+WHERE+%7B+GRAPH+?g+%7B+?s+?p+?o+%7D+%7D'"
echo
echo "Esegui le query demo:"
echo "  bash scripts/run_sparql_demo.sh"
