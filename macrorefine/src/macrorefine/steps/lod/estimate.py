"""EstimateAnnualAmount — ricostruisce l'importo annuo da `n × media × 13`.

I CSV INPS "regime di liquidazione" e "serie storica" non riportano
l'importo complessivo annuo (privacy statistica o non disponibile per
storia: cfr. PROGETTO_CONTESTO.md sez. 6 + sez. 9 "Privacy statistica").
Lo ricostruiamo come:

    importo_annuo = numero_pensioni × importo_medio_mensile × 13

dove 13 = 12 mensilità + 13esima. È una **stima derivata** dichiarata
esplicitamente nel grafo finale come `sdmx-attribute:obsStatus = sdmx-code:obsStatus-E`
+ `prov:wasDerivedFrom` verso le due osservazioni sorgenti (vedi sez. 10.14
del file di contesto, pattern "osservazione derivata" — i 4 punti di applicazione).

Questo step lavora a livello tabellare (DataFrame): crea una nuova colonna
con il valore stimato. La semantica RDF "Estimated + wasDerivedFrom" viene
applicata a livello di Recipe quando si emette il Turtle, leggendo l'history
generata da questo step.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from macrorefine.history import StepRecord
from macrorefine.step import PipelineStep

if TYPE_CHECKING:
    from macrorefine.dataset import Dataset


class EstimateAnnualAmount(PipelineStep):
    """Stima l'importo annuo come `count × monthly × months × scale`.

    Args:
        count_col: nome colonna con il conteggio (es. "numero_pensioni").
        monthly_col: nome colonna con l'importo medio mensile (es. "importo_medio_mensile").
        output_col: nome della nuova colonna da creare.
        months: moltiplicatore di mensilità (default 13 = 12 + 13esima).
        scale: fattore di scala finale (default 1.0 → euro; usa 1e-6 per
            output in milioni di euro, coerente col cubo 1 che già lo fa).

    Le righe con NaN in `count_col` o `monthly_col` producono NaN in output
    (pandas propaga NaN nelle operazioni aritmetiche).
    """

    def __init__(
        self,
        count_col: str,
        monthly_col: str,
        output_col: str,
        months: int = 13,
        scale: float = 1.0,
    ) -> None:
        super().__init__()
        if months <= 0:
            raise ValueError(f"`months` deve essere > 0 (ricevuto {months})")
        self.count_col = count_col
        self.monthly_col = monthly_col
        self.output_col = output_col
        self.months = months
        self.scale = float(scale)

    def apply(self, dataset: "Dataset") -> "Dataset":
        df = dataset.to_pandas()

        # Verifica esistenza delle colonne sorgenti (fail-fast con messaggio chiaro)
        missing = [c for c in (self.count_col, self.monthly_col) if c not in df.columns]
        if missing:
            raise KeyError(
                f"EstimateAnnualAmount: colonne sorgenti mancanti nel dataset: {missing}. "
                f"Disponibili: {list(df.columns)}"
            )

        # Calcolo: NaN-propagating, coerente con pandas semantics
        df[self.output_col] = (
            df[self.count_col] * df[self.monthly_col] * self.months * self.scale
        )

        # Metriche per audit trail
        non_null_rows = int(df[self.output_col].notna().sum())
        raw_sum = df[self.output_col].sum(skipna=True)
        estimated_sum: float | None = (
            float(raw_sum) if pd.notna(raw_sum) else None
        )

        record = StepRecord(
            name=self.name,
            params={
                "count_col": self.count_col,
                "monthly_col": self.monthly_col,
                "output_col": self.output_col,
                "months": self.months,
                "scale": self.scale,
            },
            metrics={
                "input_rows": int(len(df)),
                "non_null_rows": non_null_rows,
                "estimated_sum": estimated_sum,
            },
        )
        return dataset.with_data(df, step_record=record)
