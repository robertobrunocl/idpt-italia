#!/usr/bin/env bash
# scripts/setup.sh — Setup dell'ambiente di sviluppo per il progetto idpt-italia.
#
# Esegui questo script UNA volta sul tuo Mac dalla root del progetto:
#   bash scripts/setup.sh
#
# Crea:
#  - .venv/                  virtualenv Python con macrorefine editable + deps
#  - tools/apache-jena-fuseki-<ver>/   binario Fuseki scaricato
#
# Richiede: Python ≥ 3.10, Java 17+, bash.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
FUSEKI_VERSION="${FUSEKI_VERSION:-5.2.0}"
FUSEKI_TGZ="apache-jena-fuseki-${FUSEKI_VERSION}.tar.gz"
FUSEKI_URL="https://archive.apache.org/dist/jena/binaries/${FUSEKI_TGZ}"
FUSEKI_DIR="tools/apache-jena-fuseki-${FUSEKI_VERSION}"

echo "=== Setup idpt-italia ==="
echo "Root: $PROJECT_ROOT"
echo "Python: $($PYTHON_BIN --version)"
echo

# ---- venv ----
if [[ ! -d ".venv" ]]; then
  echo "[1/3] Creo virtualenv .venv/"
  "$PYTHON_BIN" -m venv .venv
else
  echo "[1/3] .venv/ già esistente, skip"
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "[2/3] Installo macrorefine (editable) + requirements.txt"
pip install --upgrade pip >/dev/null
pip install -e ./macrorefine
pip install -r requirements.txt

# ---- Fuseki ----
mkdir -p tools
if [[ ! -d "$FUSEKI_DIR" ]]; then
  echo "[3/3] Scarico Apache Jena Fuseki $FUSEKI_VERSION"
  if ! command -v java >/dev/null 2>&1; then
    echo "  ⚠ Java non trovato nel PATH. Installalo (Temurin/OpenJDK 17+) e rilancia."
    echo "    Su macOS: brew install --cask temurin@21"
    exit 1
  fi
  JAVA_MAJOR=$(java -version 2>&1 | awk -F'"' '/version/ {print $2}' | awk -F. '{print ($1 == "1") ? $2 : $1}')
  if [[ -z "$JAVA_MAJOR" || "$JAVA_MAJOR" -lt 17 ]]; then
    echo "  ⚠ Java troppo vecchio: rilevata versione major=$JAVA_MAJOR (Fuseki 5.x richiede ≥ 17)."
    echo "    Su macOS: brew install --cask temurin@21"
    echo "    Dopo l'install, riavvia il terminale e rilancia bash scripts/setup.sh"
    exit 1
  fi
  echo "  ✓ Java $JAVA_MAJOR OK"
  curl -fSL "$FUSEKI_URL" -o "tools/$FUSEKI_TGZ"
  tar -xzf "tools/$FUSEKI_TGZ" -C tools/
  rm "tools/$FUSEKI_TGZ"
  echo "  ✓ Fuseki in $FUSEKI_DIR"
else
  echo "[3/3] $FUSEKI_DIR già esistente, skip"
fi

echo
echo "=== Setup completato ==="
echo "Attiva il venv con:   source .venv/bin/activate"
echo "Avvia Fuseki con:     bash scripts/start_fuseki.sh"
echo "Smoke test SPARQL:    python scripts/smoke_test_agid.py"
