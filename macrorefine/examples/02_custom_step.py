"""
Esempio 2: Creare uno Step custom per un caso specifico.

Mostra come scrivere step ad hoc per esigenze particolari di un dataset.
"""
import pandas as pd

from macrorefine import Dataset, Pipeline, PipelineStep
from macrorefine.history import StepRecord
from macrorefine.steps import NormalizeColumnNames


# --- Step custom 1: normalizza i nomi delle città ---
class NormalizeCity(PipelineStep):
    """Strip + Title Case sulla colonna 'city'."""

    def apply(self, dataset: Dataset) -> Dataset:
        df = dataset.to_pandas()
        df["city"] = df["city"].str.strip().str.title()
        return dataset.with_data(df, step_name=self.name)


# --- Step custom 2: parametrizzato ---
class FormatItalianPhone(PipelineStep):
    """
    Pulisce un numero di telefono italiano:
    - rimuove caratteri non numerici
    - rimuove prefisso internazionale '00' se presente
    - rimuove prefisso paese '39' se presente
    - aggiunge il prefisso '+39 '
    """

    def __init__(self, column: str) -> None:
        super().__init__()
        self.column = column

    def _normalize(self, value: object) -> str | None:
        if value is None:
            return None
        # Tieni solo le cifre
        digits = "".join(ch for ch in str(value) if ch.isdigit())
        if not digits:
            return None
        # Rimuove prefisso internazionale '00' (es. 0039...)
        if digits.startswith("00"):
            digits = digits[2:]
        # Rimuove prefisso paese '39' (sia da +39 sia da 0039)
        if digits.startswith("39"):
            digits = digits[2:]
        if not digits:
            return None
        return f"+39 {digits}"

    def apply(self, dataset: Dataset) -> Dataset:
        df = dataset.to_pandas()
        original = df[self.column].copy()
        df[self.column] = df[self.column].apply(self._normalize)

        n_changed = int((original.fillna("") != df[self.column].fillna("")).sum())

        record = StepRecord(
            name=self.name,
            params={"column": self.column},
            metrics={"n_changed": n_changed},
        )
        return dataset.with_data(df, step_record=record)


def main() -> None:
    df = pd.DataFrame({
        "Full Name": ["Mario Rossi", "Luigi Bianchi", "Anna Verdi"],
        "City ": [" rome ", "MILAN", "naples"],
        "Phone": ["+39 333 1234567", "0039-348-9876543", "3471122334"],
    })
    ds = Dataset(df)

    pipeline = (
        Pipeline(on_error="raise")
        .add(NormalizeColumnNames())
        .add(NormalizeCity())
        .add(FormatItalianPhone(column="phone"))
    )

    clean = pipeline.run(ds)

    print("Risultato:")
    print(clean.to_pandas())
    print("\nHistory:")
    print(clean.history)


if __name__ == "__main__":
    main()