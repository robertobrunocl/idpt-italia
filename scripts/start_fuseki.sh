#!/usr/bin/env bash
# scripts/start_fuseki.sh — Avvia Fuseki locale per il progetto idpt-italia.
#
# Configurazione:
#   - Dataset name: /idpt
#   - Storage: TDB2 persistente in ./fuseki-data/
#   - SPARQL update abilitato (per i test, non per la pubblicazione)
#   - URL endpoint: http://localhost:3030/idpt/sparql

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

FUSEKI_VERSION="${FUSEKI_VERSION:-5.2.0}"
FUSEKI_DIR="tools/apache-jena-fuseki-${FUSEKI_VERSION}"

if [[ ! -d "$FUSEKI_DIR" ]]; then
  echo "⚠ Fuseki non trovato in $FUSEKI_DIR"
  echo "  Esegui prima: bash scripts/setup.sh"
  exit 1
fi

# Check Java ≥ 17 (Fuseki 5.x richiede Java 17+).
if ! command -v java >/dev/null 2>&1; then
  echo "⚠ Java non trovato nel PATH."
  echo "  Installa con: brew install --cask temurin@21"
  exit 1
fi

JAVA_MAJOR=$(java -version 2>&1 | awk -F'"' '/version/ {print $2}' | awk -F. '{print ($1 == "1") ? $2 : $1}')
if [[ -z "$JAVA_MAJOR" || "$JAVA_MAJOR" -lt 17 ]]; then
  echo "⚠ Java troppo vecchio: rilevata versione major=$JAVA_MAJOR (richiesto ≥ 17)."
  echo "  Fuseki 5.x non parte. Installa Java 17+ con:"
  echo "    brew install --cask temurin@21"
  echo "  Poi verifica con: java -version"
  exit 1
fi

mkdir -p fuseki-data

echo "Avvio Fuseki su http://localhost:3030/"
echo "Endpoint SPARQL:  http://localhost:3030/idpt/sparql"
echo "Endpoint update:  http://localhost:3030/idpt/update"
echo "UI admin:         http://localhost:3030/"
echo
echo "Ctrl+C per fermarlo."
echo

exec "$FUSEKI_DIR/fuseki-server" \
  --update \
  --tdb2 \
  --loc=./fuseki-data \
  --set tdb:unionDefaultGraph=true \
  /idpt
