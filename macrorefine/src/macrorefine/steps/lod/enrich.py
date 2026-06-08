"""EnrichWithStaticMapping — popola N nuove colonne da un dizionario di lookup.

Pattern riusabile per i cubi del progetto idpt-italia che devono mappare un
codice locale (es. ``DATA_TYPE = "POP014"``) a una URI SKOS Concept (es.
``idpt:ind-pop014``) e a un literal ausiliario (es. ``"%"`` per unitMeasure).

Esempio d'uso:

    step = EnrichWithStaticMapping(
        source_column="DATA_TYPE",
        mappings={
            "indicatore_uri":       {"POP014": "...", "AGEINDEX": "...", ...},
            "unit_measure_literal": {"POP014": "%", "MEANAGEP": "anni", ...},
        },
    )

Aggiunge 2 nuove colonne ``indicatore_uri`` e ``unit_measure_literal`` al df,
popolate via lookup su ``DATA_TYPE``.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from macrorefine.history import StepRecord
from macrorefine.step import PipelineStep

if TYPE_CHECKING:
    from macrorefine.dataset import Dataset


class EnrichWithStaticMapping(PipelineStep):
    """Aggiunge N colonne al df via lookup statici su una source_column.

    Args:
        source_column: nome colonna da cui leggere il valore di lookup.
        mappings: ``{nome_colonna_target: {source_value: target_value}}``.
            Le keys del dict esterno sono i nomi delle nuove colonne da
            aggiungere; le keys dei dict interni sono i valori possibili
            di ``source_column``, le values sono i valori target.
        raise_on_unmatched: se True, solleva ValueError se trova un
            ``source_value`` non presente in tutti i mapping. Se False,
            lascia NaN nelle colonne target dove manca il mapping.
            Default True (fail-fast per evitare bug silenziosi).

    Metriche StepRecord:
        - ``input_rows``: righe in input
        - ``unmatched_source_values``: lista valori non mappati (vuota se OK)
        - ``unique_source_values``: numero valori distinti in source_column
        - ``target_columns_added``: nomi delle colonne aggiunte
    """

    def __init__(
        self,
        source_column: str,
        mappings: dict[str, dict[str, str]],
        raise_on_unmatched: bool = True,
    ) -> None:
        super().__init__()
        self.source_column = source_column
        self.mappings = {k: dict(v) for k, v in mappings.items()}
        self.raise_on_unmatched = raise_on_unmatched

    def apply(self, dataset: "Dataset") -> "Dataset":
        df = dataset.to_pandas()

        if self.source_column not in df.columns:
            raise KeyError(
                f"EnrichWithStaticMapping: source_column '{self.source_column}' "
                f"non presente. Disponibili: {list(df.columns)}"
            )

        # Identifica unmatched aggregati su tutti i mapping
        all_source_keys: set[str] = set()
        for col_map in self.mappings.values():
            all_source_keys.update(col_map.keys())
        actual_source_values = set(df[self.source_column].dropna().astype(str).unique())
        unmatched = sorted(actual_source_values - all_source_keys)

        if unmatched and self.raise_on_unmatched:
            raise ValueError(
                f"EnrichWithStaticMapping: valori di '{self.source_column}' "
                f"non risolvibili: {unmatched[:10]}"
                f"{'...' if len(unmatched) > 10 else ''}. "
                f"Aggiungi mapping o disabilita raise_on_unmatched."
            )

        # Aggiungi le colonne target via map (NaN dove non c'è match)
        for target_col, mapping in self.mappings.items():
            df[target_col] = df[self.source_column].map(mapping)

        record = StepRecord(
            name=self.name,
            params={
                "source_column": self.source_column,
                "target_columns": list(self.mappings.keys()),
                "mappings_size_per_target": {
                    k: len(v) for k, v in self.mappings.items()
                },
                "raise_on_unmatched": self.raise_on_unmatched,
            },
            metrics={
                "input_rows": int(len(df)),
                "unique_source_values": len(actual_source_values),
                "unmatched_source_values": unmatched,
                "target_columns_added": list(self.mappings.keys()),
            },
        )
        return dataset.with_data(df, step_record=record)
