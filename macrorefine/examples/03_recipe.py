"""
Esempio 3: Recipe per dataset ricorrenti.

Quando lo stesso tipo di dataset arriva regolarmente (es. export mensile),
incapsula la pipeline in una Recipe parametrizzabile.
"""
import pandas as pd

from macrorefine import Dataset, Pipeline, PipelineStep, Recipe
from macrorefine.steps import (
    DropDuplicateRows,
    DropEmptyColumns,
    FillMissing,
    NormalizeColumnNames,
)


# Step custom riutilizzabile in più recipe
class StripStringColumns(PipelineStep):
    """Rimuove gli spazi iniziali/finali da tutte le colonne testuali."""

    def apply(self, dataset: Dataset) -> Dataset:
        df = dataset.to_pandas()
        text_cols = df.select_dtypes(include=["object", "string"]).columns
        for col in text_cols:
            # .str funziona sia su object sia su string dtype
            df[col] = df[col].str.strip()
        return dataset.with_data(df, step_name=self.name)


class CRMRecipe(Recipe):
    """
    Pipeline standard per gli export CRM mensili.

    Args:
        fill_age_strategy: "mean" o "median" per riempire l'età.
        drop_duplicates: se True rimuove le righe duplicate.
    """

    def __init__(
        self,
        fill_age_strategy: str = "median",
        drop_duplicates: bool = True,
    ) -> None:
        self.fill_age_strategy = fill_age_strategy
        self.drop_duplicates = drop_duplicates

    def build(self) -> Pipeline:
        pipeline = (
            Pipeline(on_error="raise")
            .add(NormalizeColumnNames())
            .add(DropEmptyColumns())
            .add(StripStringColumns())
            .add(FillMissing(columns=["age"], strategy=self.fill_age_strategy))
        )
        if self.drop_duplicates:
            pipeline.add(DropDuplicateRows())
        return pipeline


def main() -> None:
    # Simuliamo due export mensili dello stesso formato
    january = Dataset(pd.DataFrame({
        "ID": [1, 2, 3, 3],
        "Full Name": [" Alice ", "Bob", "Charlie", "Charlie"],
        "Age": [30, None, 25, 25],
        "Empty": [None, None, None, None],
    }))

    february = Dataset(pd.DataFrame({
        "ID": [10, 11, 12],
        "Full Name": ["Diana", " Eve ", "Frank"],
        "Age": [22, None, 45],
        "Empty": [None, None, None],
    }))

    # Stessa recipe applicata a entrambi
    recipe = CRMRecipe(fill_age_strategy="median", drop_duplicates=True)

    jan_clean = recipe.apply(january)
    feb_clean = recipe.apply(february)

    print("=== Gennaio (pulito) ===")
    print(jan_clean.to_pandas())
    print(f"\nStep applicati: {[r.name for r in jan_clean.history]}")

    print("\n=== Febbraio (pulito) ===")
    print(feb_clean.to_pandas())
    print(f"\nStep applicati: {[r.name for r in feb_clean.history]}")


if __name__ == "__main__":
    main()