"""scripts/finalize_namespace.py — Sostituisce il placeholder idpt: con l'URL definitivo.

Decisione metodologica δ+β del check-point ontologico (sez. 4 di
PROGETTO_CONTESTO.md): durante lo sviluppo il namespace `idpt:` è
``https://example.org/idpt/``; al deploy GitHub Pages diventa
``https://robertobrunocl.github.io/idpt-italia/`` (o altro URL stabile).

Questo script applica il find-and-replace globale su tutti i file TTL
in ``output/`` (sia statici sia quelli emessi da Recipe) e nei file di
configurazione.

NB: NON tocca i file Python (le Recipe usano ``V.IDPT_NS = "https://example.org/idpt/"``
come placeholder; per cambiare deploy si modifica solo ``scripts/recipes/idpt_vocab.py``).

Uso:
    # Anteprima (non scrive nulla)
    python scripts/finalize_namespace.py --new-base https://robertobruno.github.io/idpt-italia/ --dry-run

    # Esecuzione effettiva
    python scripts/finalize_namespace.py --new-base https://robertobruno.github.io/idpt-italia/

    # Reset (riporta tutto a placeholder)
    python scripts/finalize_namespace.py --new-base https://example.org/idpt/
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OLD_BASE = "https://example.org/idpt/"

# File da processare (find-and-replace solo del namespace idpt:)
TARGETS = [
    "output/observations",
    "output/computed",
    "output/mappings",
    "output/vocabularies",
    "output/dataset",
    "output/dist",
]


def replace_in_file(path: Path, old: str, new: str, dry_run: bool) -> int:
    """Ritorna numero di sostituzioni effettuate (o pianificate in dry-run)."""
    if not path.is_file():
        return 0
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return 0
    count = text.count(old)
    if count == 0:
        return 0
    if not dry_run:
        new_text = text.replace(old, new)
        path.write_text(new_text, encoding="utf-8")
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--new-base", required=True,
        help="Nuovo URL del namespace idpt:, es. https://robertobrunocl.github.io/idpt-italia/"
    )
    parser.add_argument(
        "--old-base", default=OLD_BASE,
        help=f"URL placeholder da sostituire (default {OLD_BASE})"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Stampa cosa farebbe senza modificare i file"
    )
    args = parser.parse_args()

    new_base = args.new_base
    if not new_base.endswith("/"):
        new_base += "/"
    old_base = args.old_base
    if not old_base.endswith("/"):
        old_base += "/"

    print(f"=== Finalize namespace ===")
    print(f"OLD: {old_base}")
    print(f"NEW: {new_base}")
    print(f"Mode: {'DRY-RUN (anteprima)' if args.dry_run else 'WRITE (modifica file)'}")
    print()

    total_files = 0
    total_subs = 0
    for target in TARGETS:
        target_path = PROJECT_ROOT / target
        if not target_path.exists():
            continue
        for ttl in sorted(target_path.rglob("*.ttl")):
            n = replace_in_file(ttl, old_base, new_base, args.dry_run)
            if n > 0:
                total_files += 1
                total_subs += n
                print(f"  {n:>5,} sostituzioni  {ttl.relative_to(PROJECT_ROOT)}")

    print()
    print(f"Totale: {total_subs:,} sostituzioni in {total_files} file"
          f"{' (dry-run, niente modificato)' if args.dry_run else ''}")

    if not args.dry_run and total_subs > 0:
        print()
        print("Prossimi passi:")
        print(f"  1. Modifica anche scripts/recipes/idpt_vocab.py:")
        print(f'       IDPT_NS = "{new_base}"')
        print(f"  2. Ricarica Fuseki:    bash scripts/load_fuseki.sh")
        print(f"  3. Rigenera deliverable (se necessario)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
