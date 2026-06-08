#!/usr/bin/env bash
# scripts/run_sparql_demo.sh — Esegue le 10 query SPARQL di demo contro Fuseki.
#
# Pre-requisito:
#   1. Fuseki avviato:   bash scripts/start_fuseki.sh
#   2. Grafi caricati:   bash scripts/load_fuseki.sh
#
# Output: per ogni query stampa intestazione (commento .rq) + max 15 righe
# risultati in formato CSV.
#
# Uso:
#   bash scripts/run_sparql_demo.sh              # esegue tutte le 10 query
#   bash scripts/run_sparql_demo.sh q03          # esegue solo le query col nome che contiene "q03"

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

FUSEKI_ENDPOINT="${FUSEKI_ENDPOINT:-http://localhost:3030/idpt}"
SPARQL_URL="$FUSEKI_ENDPOINT/sparql"

filter="${1:-}"

if ! curl -fs "$SPARQL_URL?query=ASK%20%7B%7D" >/dev/null 2>&1; then
  echo "⚠ Fuseki non raggiungibile su $FUSEKI_ENDPOINT"
  echo "  Avvialo con:    bash scripts/start_fuseki.sh"
  echo "  Carica dati con: bash scripts/load_fuseki.sh"
  exit 1
fi

QUERY_DIR="scripts/sparql"
QUERIES=$(ls "$QUERY_DIR"/q[0-9]*_*.rq 2>/dev/null | sort)
if [[ -z "$QUERIES" ]]; then
  echo "⚠ Nessuna query trovata in $QUERY_DIR/q*_*.rq"
  exit 1
fi

for query_file in $QUERIES; do
  query_name=$(basename "$query_file" .rq)
  if [[ -n "$filter" && "$query_name" != *"$filter"* ]]; then
    continue
  fi

  echo
  echo "================================================================"
  echo "$query_name"
  echo "================================================================"
  # Stampa commento di testa
  awk '/^#/{print substr($0, 3); next} /^[[:space:]]*$/{exit}' "$query_file"
  echo "----------------------------------------------------------------"

  response=$(curl -fsS -X POST \
    --data-urlencode "query@$query_file" \
    -H "Accept: text/csv" \
    "$SPARQL_URL")

  echo "$response" | head -15
  total=$(echo "$response" | tail -n +2 | wc -l | tr -d ' ')
  echo "  → totale righe: $total"
done

echo
echo "=== Demo SPARQL completata ==="
