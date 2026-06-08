"""
Esempio 6: Conversione tipi e parsing date.

Caso d'uso comune: dataset CSV in cui i numeri sono salvati come stringhe
e le date sono in formato non standard.
"""
import pandas as pd

from macrorefine import Dataset, Pipeline
from macrorefine.steps import (
    CastTypes,
    NormalizeColumnNames,
    ParseDates,
    RenameColumns,
)


def main() -> None:
    df = pd.DataFrame({
        "Customer ID": ["1", "2", "3", "4"],
        "Revenue": ["100.50", "250.75", "bad_value", "75.20"],
        "Created At": ["15/01/2024", "20/02/2024", "10/03/2024", "05/04/2024"],
        "Active": ["1", "0", "1", "1"],
    })
    ds = Dataset(df)

    print("=== ORIGINALE ===")
    print(ds.to_pandas())
    print("\nDtypes:")
    print(ds.to_pandas().dtypes)

    pipeline = (
        Pipeline(on_error="raise")
        .add(NormalizeColumnNames())
        .add(RenameColumns(mapping={"customer_id": "id"}))
        .add(CastTypes(mapping={"id": "int", "active": "bool"}))
        .add(CastTypes(mapping={"revenue": "float"}, errors="coerce"))
        .add(ParseDates(columns="created_at", format="%d/%m/%Y"))
    )

    clean = pipeline.run(ds)

    print("\n=== PULITO ===")
    print(clean.to_pandas())
    print("\nDtypes:")
    print(clean.to_pandas().dtypes)

    print("\n=== HISTORY ===")
    for record in clean.history:
        print(f"  - {record.name}  params={record.params}")


if __name__ == "__main__":
    main()