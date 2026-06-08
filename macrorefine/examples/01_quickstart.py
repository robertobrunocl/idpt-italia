"""
Esempio 1: Quickstart end-to-end.

Mostra il flusso base: caricamento → profiling → pipeline → output.
"""
import pandas as pd

from macrorefine import Dataset, Pipeline
from macrorefine.steps import (
    DropDuplicateRows,
    DropEmptyColumns,
    FillMissing,
    NormalizeColumnNames,
)


def main() -> None:
    # Dataset sporco di esempio
    df = pd.DataFrame({
        "ID": [1, 2, 3, 3, 4, 5],
        "Full Name": ["Alice", "Bob", "Charlie", "Charlie", "Diana", "Eve"],
        "Age": [30, None, 25, 25, 40, None],
        "EmptyCol": [None, None, None, None, None, None],
        "City ": ["Rome", "Milan", "Naples", "Naples", "Turin", "Bologna"],
    })
    ds = Dataset(df)

    print("=" * 60)
    print("DATASET ORIGINALE")
    print("=" * 60)
    print(ds.to_pandas())
    print(f"\nShape: {ds.shape}")

    print("\n" + "=" * 60)
    print("PROFILING")
    print("=" * 60)
    print(ds.profile())

    print("\n" + "=" * 60)
    print("PIPELINE")
    print("=" * 60)
    clean = (
        Pipeline(on_error="raise")
        .add(NormalizeColumnNames())
        .add(DropEmptyColumns())
        .add(DropDuplicateRows())
        .add(FillMissing(columns=["age"], strategy="median"))
        .run(ds)
    )

    print(clean.to_pandas())

    print("\n" + "=" * 60)
    print("HISTORY")
    print("=" * 60)
    print(clean.history)

    # Verifica immutabilità: il dataset originale non è cambiato
    print("\n" + "=" * 60)
    print("Il dataset originale non è stato modificato (immutabilità):")
    print("=" * 60)
    print(f"Colonne originali: {ds.columns}")
    print(f"Colonne dopo pipeline: {clean.columns}")


if __name__ == "__main__":
    main()