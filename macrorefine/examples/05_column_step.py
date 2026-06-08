"""
Esempio 5: ColumnStep — step ad hoc per colonne specifiche.

Questo esempio mostra come `ColumnStep` riduce drasticamente il boilerplate
quando devi creare step custom che operano su singole colonne (caso comune
quando un dataset ha campi con formattazioni particolari).
"""
import unicodedata

import pandas as pd

from macrorefine import ColumnStep, Dataset, Pipeline
from macrorefine.steps import NormalizeColumnNames


# --- Step 1: rimuove gli accenti (riusabile su qualsiasi colonna testuale) ---
class StripAccents(ColumnStep):
    def transform_column(self, series, column_name):
        return series.apply(
            lambda x: unicodedata.normalize("NFKD", str(x))
            .encode("ascii", "ignore")
            .decode()
        )


# --- Step 2: title case ---
class TitleCase(ColumnStep):
    def transform_column(self, series, column_name):
        return series.str.strip().str.title()


# --- Step 3: telefono italiano (versione con ColumnStep, niente boilerplate) ---
class FormatItalianPhone(ColumnStep):
    def transform_column(self, series, column_name):
        def normalize(value):
            if value is None or pd.isna(value):
                return None
            digits = "".join(ch for ch in str(value) if ch.isdigit())
            if digits.startswith("00"):
                digits = digits[2:]
            if digits.startswith("39"):
                digits = digits[2:]
            return f"+39 {digits}" if digits else None

        return series.apply(normalize)


# --- Step 4: logica condizionale per nome colonna ---
class SmartTrim(ColumnStep):
    """Esempio di step che usa il nome della colonna per logica condizionale.

    Tronca le stringhe a lunghezze diverse a seconda della colonna.
    """

    LIMITS = {"name": 50, "address": 100, "notes": 200}

    def transform_column(self, series, column_name):
        limit = self.LIMITS.get(column_name, 30)
        return series.astype(str).str.slice(0, limit)


def main() -> None:
    df = pd.DataFrame({
        "Full Name": [" mario rossi ", "LUIGI BIANCHI", "anna verdi"],
        "City": ["Café", "Münich", "Rome"],
        "Phone": ["+39 333 1234567", "0039-348-9876543", "3471122334"],
        "Notes": ["a" * 300, "short note", "b" * 250],
    })
    ds = Dataset(df)

    print("=== ORIGINALE ===")
    print(ds.to_pandas())

    pipeline = (
        Pipeline(on_error="raise")
        .add(NormalizeColumnNames())
        .add(StripAccents(columns="city"))
        .add(TitleCase(columns=["full_name", "city"]))
        .add(FormatItalianPhone(columns="phone"))
        .add(SmartTrim(columns="notes"))
    )

    clean = pipeline.run(ds)

    print("\n=== PULITO ===")
    print(clean.to_pandas())

    print("\n=== HISTORY ===")
    for record in clean.history:
        print(f"  - {record.name}  params={record.params}")


if __name__ == "__main__":
    main()