"""Step di aggregazione domain-specific (Sardegna INPS, comuni MEF, ecc.).

I CSV INPS "vigenti per residenza" del 2026 riportano 110 entry territoriali:
107 province AGID standard + 2 PA (Bolzano, Trento) + 4 ex-province sarde
istituite nel 2005 e dissolte nel 2016 (Carbonia-Iglesias, Medio Campidano,
Ogliastra, Olbia-Tempio). Le ex-province non sono nel vocabolario AGID
attuale; vanno aggregate sulle 5 province sarde correnti secondo il mapping
definito al check-point ontologico (PROGETTO_CONTESTO.md sez. 4 + 10.9):

    Cagliari               → Cagliari            (092)
    Carbonia -Iglesias     → Sud Sardegna        (111)
    Medio Campidano        → Sud Sardegna        (111)
    Nuoro                  → Nuoro               (091)
    Ogliastra              → Nuoro               (091)
    Olbia -Tempio          → Sassari             (090)
    Oristano               → Oristano            (095)
    Sassari                → Sassari             (090)

Modalità ``snapshot`` (implementata qui): trasforma 8 righe in 5 righe.
- Misure di conteggio: SOMMA semplice (es. numero pensioni).
- Misure di importo medio mensile: MEDIA PESATA (peso = numero pensioni).
- Misure di importo aggregato annuo (es. milioni di euro): SOMMA semplice.
- Il valore della colonna provincia viene sostituito col nome AGID canonico.

Modalità ``mark_serie_storica`` (NOT YET IMPLEMENTED): per il CSV serie storica
1998-2026, le ex-province non sono fisicamente nel CSV (già aggregato sulle
106 sedi attuali). Per gli anni 2005-2011 va aggiunta una colonna di stato
``_aggregation_status = "estimated_pre_2012"`` che la Recipe userà per emettere
``sdmx-attribute:obsStatus sdmx-code:obsStatus-E`` + ``prov:wasDerivedFrom``
in fase di materializzazione RDF. Modalità rimandata al blocco 3 / Fase 5.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from macrorefine.history import StepRecord
from macrorefine.step import PipelineStep

if TYPE_CHECKING:
    from macrorefine.dataset import Dataset


# Mapping fisso 8 nomi INPS → nome AGID canonico (e relativo codice ISTAT).
# Le 4 ex-province (Carbonia-Iglesias, Medio Campidano, Ogliastra, Olbia-Tempio)
# vengono dissolte; le altre 4 (Cagliari, Nuoro, Oristano, Sassari) restano ma
# possono assorbire righe di ex-province.
SARDINIA_AGGREGATION: dict[str, tuple[str, str]] = {
    # INPS name (case-sensitive)       → (AGID canonical name, codice ISTAT)
    "Cagliari":              ("Cagliari",     "092"),
    "Carbonia -Iglesias":    ("Sud Sardegna", "111"),
    "Carbonia-Iglesias":     ("Sud Sardegna", "111"),  # variante senza spazio
    "Medio Campidano":       ("Sud Sardegna", "111"),
    "Nuoro":                 ("Nuoro",        "091"),
    "Ogliastra":             ("Nuoro",        "091"),
    "Olbia -Tempio":         ("Sassari",      "090"),
    "Olbia-Tempio":          ("Sassari",      "090"),  # variante senza spazio
    "Oristano":              ("Oristano",     "095"),
    "Sassari":               ("Sassari",      "090"),
}


class AggregateSardiniaProvinces(PipelineStep):
    """Aggrega le 8 ex/sard province INPS sulle 5 province AGID attuali.

    Args:
        province_column: nome colonna con il nome provincia.
        count_columns: colonne da sommare (conteggio pensioni). Saranno
            sommate gruppo per gruppo, con propagazione NaN-aware
            (``sum(skipna=True)``).
        weight_pairs: dizionario ``{colonna_media: colonna_peso}``. Per
            ciascuna coppia, calcola la media pesata della "colonna_media"
            usando la "colonna_peso" come peso. Pesi NaN → riga ignorata
            nella media. Tipicamente weight_pairs={"importo_medio_mensile":
            "numero_pensioni"}.
        sum_columns: altre colonne da sommare oltre a count_columns (es.
            "importo_complessivo_annuo"). Default: lista vuota.
        mode: per ora supporta solo "snapshot".

    Output: il df ha (rows_before - 3) righe se tutte le 8 sarde sono presenti
    (8 collassano in 5). I valori della province_column sono sostituiti col
    nome canonico AGID. Le colonne non-Sardegna restano invariate.

    Test di sanità (in test):
    - Totale numero pensioni pre = post (preservazione)
    - Importo annuo pre = post (preservazione)
    - Le 4 ex-province non compaiono più nel df di output
    """

    SUPPORTED_MODES = ("snapshot",)

    def __init__(
        self,
        province_column: str,
        count_columns: list[str],
        weight_pairs: dict[str, str] | None = None,
        sum_columns: list[str] | None = None,
        mode: str = "snapshot",
    ) -> None:
        super().__init__()
        if mode not in self.SUPPORTED_MODES:
            raise ValueError(
                f"mode='{mode}' non supportato. Disponibili: {self.SUPPORTED_MODES}"
            )
        self.province_column = province_column
        self.count_columns = list(count_columns)
        self.weight_pairs = dict(weight_pairs) if weight_pairs else {}
        self.sum_columns = list(sum_columns) if sum_columns else []
        self.mode = mode

    def apply(self, dataset: "Dataset") -> "Dataset":
        df = dataset.to_pandas()

        if self.province_column not in df.columns:
            raise KeyError(
                f"AggregateSardiniaProvinces: colonna provincia "
                f"'{self.province_column}' non presente. "
                f"Disponibili: {list(df.columns)}"
            )

        # Verifica esistenza colonne numeriche dichiarate
        required = (
            self.count_columns
            + list(self.weight_pairs.keys())
            + list(self.weight_pairs.values())
            + self.sum_columns
        )
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise KeyError(
                f"AggregateSardiniaProvinces: colonne mancanti: {missing}"
            )

        # Maschera delle righe sarde da aggregare
        sardinia_mask = df[self.province_column].isin(SARDINIA_AGGREGATION.keys())
        sardinia_rows = df[sardinia_mask].copy()
        other_rows = df[~sardinia_mask].copy()

        rows_collapsed_input = int(sardinia_mask.sum())

        # Per ogni riga sarda, mappiamo al nome canonico AGID
        sardinia_rows["_agid_canonical"] = sardinia_rows[self.province_column].map(
            lambda n: SARDINIA_AGGREGATION[n][0]
        )

        # Aggregazione per nome AGID canonico
        agg_groups = []
        for agid_name, group in sardinia_rows.groupby("_agid_canonical", sort=False):
            agg_row: dict[str, object] = {}
            # Copia colonne non-numeriche dal primo elemento del gruppo
            # (assunzione: dimensioni/etichette uguali per il blocco sardo)
            for col in df.columns:
                if col not in (self.count_columns + self.sum_columns
                               + list(self.weight_pairs.keys())):
                    agg_row[col] = group.iloc[0][col]
            # Sostituisco il nome provincia con quello canonico
            agg_row[self.province_column] = agid_name

            # Conteggi: somma NaN-safe
            for col in self.count_columns:
                agg_row[col] = group[col].sum(skipna=True)

            # Altre somme
            for col in self.sum_columns:
                agg_row[col] = group[col].sum(skipna=True)

            # Medie pesate
            for value_col, weight_col in self.weight_pairs.items():
                values = group[value_col].astype(float)
                weights = group[weight_col].astype(float)
                # Maschera NaN su entrambi i lati
                valid = values.notna() & weights.notna() & (weights > 0)
                if valid.any():
                    w_sum = weights[valid].sum()
                    agg_row[value_col] = (
                        (values[valid] * weights[valid]).sum() / w_sum
                        if w_sum > 0 else np.nan
                    )
                else:
                    agg_row[value_col] = np.nan

            agg_groups.append(agg_row)

        # Costruisco il df aggregato
        if agg_groups:
            agg_df = pd.DataFrame(agg_groups, columns=df.columns)
            # Drop la colonna temporanea
            agg_df = agg_df.drop(columns=["_agid_canonical"], errors="ignore")
            result = pd.concat([other_rows, agg_df], ignore_index=True)
        else:
            # Nessuna riga sarda nel df: nulla da fare
            result = other_rows

        record = StepRecord(
            name=self.name,
            params={
                "province_column": self.province_column,
                "count_columns": list(self.count_columns),
                "weight_pairs": dict(self.weight_pairs),
                "sum_columns": list(self.sum_columns),
                "mode": self.mode,
                "aggregation_mapping_size": len(SARDINIA_AGGREGATION),
            },
            metrics={
                "rows_before": int(len(df)),
                "rows_after": int(len(result)),
                "sardinian_rows_collapsed_input": rows_collapsed_input,
                "aggregated_groups": len(agg_groups),
            },
        )
        return dataset.with_data(result, step_record=record)


# =============================================================================
# AggregateMEFRedditiByProvincia
# =============================================================================

# Default mapping {voce_short: (colonna_frequenza, colonna_ammontare)} per il
# CSV MEF redditi IRPEF comunale. Match esatto sui nomi colonne del CSV
# pubblicato dal Dipartimento delle Finanze (verificato in Fase 4 cubo 7).
DEFAULT_MEF_VOCI_COLUMNS: dict[str, tuple[str, str]] = {
    "v2": (
        "Reddito da lavoro dipendente e assimilati - Frequenza",
        "Reddito da lavoro dipendente e assimilati - Ammontare in euro",
    ),
    "v4": (
        "Reddito da lavoro autonomo (comprensivo dei valori nulli) - Frequenza",
        "Reddito da lavoro autonomo (comprensivo dei valori nulli) - Ammontare in euro",
    ),
    "v5": (
        "Reddito di spettanza dell'imprenditore in contabilita' ordinaria  (comprensivo dei valori nulli) - Frequenza",
        "Reddito di spettanza dell'imprenditore in contabilita' ordinaria  (comprensivo dei valori nulli) - Ammontare in euro",
    ),
    "v6": (
        "Reddito di spettanza dell'imprenditore in contabilita' semplificata (comprensivo dei valori nulli) - Frequenza",
        "Reddito di spettanza dell'imprenditore in contabilita' semplificata (comprensivo dei valori nulli) - Ammontare in euro",
    ),
    "v7": (
        "Reddito da partecipazione  (comprensivo dei valori nulli) - Frequenza",
        "Reddito da partecipazione  (comprensivo dei valori nulli) - Ammontare in euro",
    ),
}


class AggregateMEFRedditiByProvincia(PipelineStep):
    """Aggrega 7897 comuni MEF → 107 province + unpivot wide→long.

    Input (wide): 1 riga per comune, 10 colonne reddito (5 voci × 2 misure).
    Output (long): 1 riga per (provincia, voce) = 535 righe per il CSV MEF
    completo, con colonne: ``<sigla_column>``, ``voce_short`` (es. "v2"),
    ``voce_uri`` (URI SKOS della voce), ``frequenza_dichiaranti`` (int),
    ``ammontare_totale`` (int, euro).

    Gestisce le 2 anomalie note del CSV MEF (sez. 9 PROGETTO_CONTESTO.md):
    1. Riga sentinella ``Sigla=sentinel_sigla`` (default ``"0"``,
       ``Regione=Mancante/errata``) viene esclusa prima dell'aggregazione.
    2. Stringhe vuote ``""`` o valori non parsabili come int diventano 0 nella
       somma (somma il contributo come "voce non dichiarata").

    Args:
        voci_uri: dict ``{voce_short: uri_skos_concept}``, es.
            ``{"v2": "https://example.org/idpt/voce-redd-lavoro-dipendente", ...}``.
            Le URI sono passate dalla Recipe (importate da idpt_vocab.py) per
            evitare dipendenza ciclica macrorefine → idpt-italia.
        sigla_column: nome colonna sigla provincia (default "Sigla Provincia").
        sentinel_sigla: valore della riga sentinella da escludere (default "0").
        voci_columns: override delle colonne sorgente. Default coerente con
            CSV MEF redditi IRPEF comunale standard.

    Metriche StepRecord: ``input_rows``, ``output_rows``,
    ``rows_dropped_sentinel``, ``aggregated_provinces``, ``voci_emitted``.
    """

    def __init__(
        self,
        voci_uri: dict[str, str],
        sigla_column: str = "Sigla Provincia",
        sentinel_sigla: str = "0",
        voci_columns: dict[str, tuple[str, str]] | None = None,
    ) -> None:
        super().__init__()
        self.voci_uri = dict(voci_uri)
        self.sigla_column = sigla_column
        self.sentinel_sigla = sentinel_sigla
        self.voci_columns = (
            dict(voci_columns) if voci_columns else dict(DEFAULT_MEF_VOCI_COLUMNS)
        )
        # Sanity check: voci_uri e voci_columns hanno le stesse chiavi
        missing_uris = set(self.voci_columns) - set(self.voci_uri)
        if missing_uris:
            raise ValueError(
                f"voci_uri non ha URI per: {sorted(missing_uris)}. "
                f"Tutte le voci_columns devono avere una voce_uri associata."
            )

    def apply(self, dataset: "Dataset") -> "Dataset":
        df = dataset.to_pandas()

        # Check colonne richieste
        missing_cols = [self.sigla_column]
        for short, (freq_col, amm_col) in self.voci_columns.items():
            missing_cols.extend([freq_col, amm_col])
        absent = [c for c in missing_cols if c not in df.columns]
        if absent:
            raise KeyError(
                f"AggregateMEFRedditiByProvincia: colonne mancanti: {absent[:5]}"
                f"{'...' if len(absent) > 5 else ''}. "
                f"Disponibili: {list(df.columns)[:5]}..."
            )

        # Step 1: drop riga sentinella
        rows_dropped_sentinel = int((df[self.sigla_column] == self.sentinel_sigla).sum())
        df = df[df[self.sigla_column] != self.sentinel_sigla].copy()

        # Step 2: cast a int le 10 colonne reddito (str "" → 0, gestione NaN)
        for short, (freq_col, amm_col) in self.voci_columns.items():
            for col in (freq_col, amm_col):
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        # Step 3: group-by sigla + unpivot wide→long
        rows = []
        for sigla, group in df.groupby(self.sigla_column, sort=True):
            for short, (freq_col, amm_col) in self.voci_columns.items():
                rows.append({
                    self.sigla_column: sigla,
                    "voce_short":            short,
                    "voce_uri":              self.voci_uri[short],
                    "frequenza_dichiaranti": int(group[freq_col].sum()),
                    "ammontare_totale":      int(group[amm_col].sum()),
                })
        result = pd.DataFrame(rows)

        record = StepRecord(
            name=self.name,
            params={
                "sigla_column": self.sigla_column,
                "sentinel_sigla": self.sentinel_sigla,
                "voci_count": len(self.voci_columns),
                "voci_short": sorted(self.voci_columns.keys()),
            },
            metrics={
                "input_rows": int(len(df) + rows_dropped_sentinel),
                "output_rows": int(len(result)),
                "rows_dropped_sentinel": rows_dropped_sentinel,
                "aggregated_provinces": int(df[self.sigla_column].nunique()),
                "voci_emitted": len(self.voci_columns),
            },
        )
        return dataset.with_data(result, step_record=record)


# =============================================================================
# UnpivotINPSPensioniVigenti
# =============================================================================

class UnpivotINPSPensioniVigenti(PipelineStep):
    """Trasforma il df INPS "vigenti residenza" da wide (5 gestioni × 3 misure
    affiancate) a long (1 riga per provincia × gestione, con 3 colonne misura).

    Args:
        province_column: nome colonna provincia (default "provincia").
        gestioni: dict ``{tipo_gestione_short: uri_skos}`` per i 5 (o 4)
            comparti INPS. Lo step assume che ci siano colonne sorgente
            ``n_{short}``, ``media_{short}``, ``annuo_{short}`` per ognuno.
        output_columns: nomi delle colonne misura in output. Default
            ``{"n_pensioni", "importo_medio_mensile", "importo_annuo_complessivo"}``.

    Output: ``len(df) * len(gestioni)`` righe, ognuna con:
        - province_column (provincia originale)
        - tipo_gestione_short (es. "PRIV")
        - tipo_gestione_uri (URI SKOS Concept)
        - n_pensioni (float)
        - importo_medio_mensile (float)
        - importo_annuo_complessivo (float, milioni di euro)
    """

    DEFAULT_OUTPUT_COLUMNS = (
        "n_pensioni",
        "importo_medio_mensile",
        "importo_annuo_complessivo",
    )
    # Per ogni gestione corrispondono 3 colonne in input: n_{short}, media_{short}, annuo_{short}
    SOURCE_COLUMN_PREFIXES = ("n_", "media_", "annuo_")

    def __init__(
        self,
        gestioni: dict[str, str],
        province_column: str = "provincia",
        output_columns: tuple[str, str, str] | None = None,
    ) -> None:
        super().__init__()
        self.gestioni = dict(gestioni)
        self.province_column = province_column
        self.output_columns = output_columns or self.DEFAULT_OUTPUT_COLUMNS
        if len(self.output_columns) != 3:
            raise ValueError("output_columns deve avere 3 nomi (n, media, annuo)")

    def apply(self, dataset: "Dataset") -> "Dataset":
        df = dataset.to_pandas()

        if self.province_column not in df.columns:
            raise KeyError(
                f"UnpivotINPSPensioniVigenti: '{self.province_column}' non in df. "
                f"Disponibili: {list(df.columns)[:10]}..."
            )

        # Verifica esistenza colonne sorgente per ogni gestione
        missing = []
        for short in self.gestioni:
            for prefix in self.SOURCE_COLUMN_PREFIXES:
                col = prefix + short
                if col not in df.columns:
                    missing.append(col)
        if missing:
            raise KeyError(
                f"UnpivotINPSPensioniVigenti: colonne mancanti: {missing}"
            )

        # Unpivot
        out_n, out_media, out_annuo = self.output_columns
        rows = []
        for _, src in df.iterrows():
            for short, uri in self.gestioni.items():
                rows.append({
                    self.province_column:   src[self.province_column],
                    "tipo_gestione_short":  short,
                    "tipo_gestione_uri":    uri,
                    out_n:                  src["n_" + short],
                    out_media:              src["media_" + short],
                    out_annuo:              src["annuo_" + short],
                })
        result = pd.DataFrame(rows)

        record = StepRecord(
            name=self.name,
            params={
                "province_column": self.province_column,
                "gestioni_short": sorted(self.gestioni.keys()),
                "output_columns": list(self.output_columns),
            },
            metrics={
                "input_rows": int(len(df)),
                "output_rows": int(len(result)),
                "gestioni_emitted": len(self.gestioni),
                "input_provinces": int(df[self.province_column].nunique()),
            },
        )
        return dataset.with_data(result, step_record=record)


# =============================================================================
# UnpivotINPSRegimeSede
# =============================================================================

class UnpivotINPSRegimeSede(PipelineStep):
    """Trasforma il df INPS "regime liquidazione" da wide (4 regimi × 2 misure
    primarie affiancate) a long stile B (1 obs = 1 misura, 3 misure totali
    incluso `importoAnnuoComplessivo` stimato come ``n × media × 13``).

    Per ogni riga input (1 sede), emette **12 righe long** (4 regimi × 3
    measureType: n_pensioni / importo_medio_mensile / importo_annuo_complessivo).

    Args:
        sede_column: nome colonna sede INPS (default "sede").
        regimi: dict ``{regime_short: (uri_skos, short_slug)}`` per i 4 regimi
            (RETR, DINI, FORNERO, CONTR). short_slug usato per URI obs.
        measure_uris: dict ``{measure_short: uri_measure_property}`` per le
            3 misure (n, med, ann).
        months: moltiplicatore mensilità per importo annuo (default 13).

    Output: 12 righe per sede con colonne:
        sede_column, regime_short_slug, regime_uri, measure_short_slug,
        measure_uri, value (float), is_estimated (bool),
        n_source_obs_uri (None per n/med, popolato per ann con la lista
        delle 2 obs sorgenti per prov:wasDerivedFrom).
    """

    DEFAULT_MEASURES = {
        "n":   ("numero_pensioni",            False),
        "med": ("importo_medio_mensile",     False),
        "ann": ("importo_annuo_complessivo", True),   # is_estimated
    }

    def __init__(
        self,
        regimi: dict[str, tuple[str, str]],    # {regime_short_in_df: (uri, slug)}
        measure_uris: dict[str, str],          # {measure_short: uri_measure}
        sede_column: str = "sede",
        months: int = 13,
    ) -> None:
        super().__init__()
        self.sede_column = sede_column
        self.regimi = dict(regimi)
        self.measure_uris = dict(measure_uris)
        self.months = months
        # Verifica chiavi attese
        missing = set(self.DEFAULT_MEASURES) - set(self.measure_uris)
        if missing:
            raise ValueError(
                f"measure_uris manca chiavi: {missing}. "
                f"Attese: {sorted(self.DEFAULT_MEASURES)}"
            )

    def apply(self, dataset: "Dataset") -> "Dataset":
        df = dataset.to_pandas()
        if self.sede_column not in df.columns:
            raise KeyError(
                f"UnpivotINPSRegimeSede: '{self.sede_column}' non in df. "
                f"Disponibili: {list(df.columns)[:10]}"
            )

        # Verifica colonne sorgente per ogni regime
        missing = []
        for regime_short in self.regimi:
            for prefix in ("n_", "media_"):
                col = prefix + regime_short
                if col not in df.columns:
                    missing.append(col)
        if missing:
            raise KeyError(f"UnpivotINPSRegimeSede: colonne mancanti: {missing}")

        rows = []
        for _, src in df.iterrows():
            sede = src[self.sede_column]
            for regime_short, (regime_uri, regime_slug) in self.regimi.items():
                n_val = src["n_" + regime_short]
                med_val = src["media_" + regime_short]
                # Misure primarie: n_pensioni + importo_medio_mensile
                rows.append({
                    self.sede_column: sede,
                    "regime_short_slug": regime_slug,
                    "regime_uri":        regime_uri,
                    "measure_short_slug": "n",
                    "measure_uri":       self.measure_uris["n"],
                    "value":             n_val,
                    "is_estimated":      False,
                })
                rows.append({
                    self.sede_column: sede,
                    "regime_short_slug": regime_slug,
                    "regime_uri":        regime_uri,
                    "measure_short_slug": "med",
                    "measure_uri":       self.measure_uris["med"],
                    "value":             med_val,
                    "is_estimated":      False,
                })
                # Misura stimata: importo_annuo_complessivo = n × media × months
                if pd.notna(n_val) and pd.notna(med_val):
                    ann_val = float(n_val) * float(med_val) * self.months
                else:
                    ann_val = None
                rows.append({
                    self.sede_column: sede,
                    "regime_short_slug": regime_slug,
                    "regime_uri":        regime_uri,
                    "measure_short_slug": "ann",
                    "measure_uri":       self.measure_uris["ann"],
                    "value":             ann_val,
                    "is_estimated":      True,
                })
        result = pd.DataFrame(rows)

        record = StepRecord(
            name=self.name,
            params={
                "sede_column": self.sede_column,
                "regimi": sorted(self.regimi.keys()),
                "measures": sorted(self.measure_uris.keys()),
                "months": self.months,
            },
            metrics={
                "input_rows": int(len(df)),
                "output_rows": int(len(result)),
                "regimi_emitted": len(self.regimi),
                "measures_per_regime": len(self.DEFAULT_MEASURES),
                "estimated_rows": int((result["is_estimated"] == True).sum()),
            },
        )
        return dataset.with_data(result, step_record=record)


# =============================================================================
# UnpivotINPSSerieStorica
# =============================================================================

class UnpivotINPSSerieStorica(PipelineStep):
    """Trasforma il df INPS "serie storica" da wide (29 anni × 2 misure
    affiancate) a long stile B (1 obs = 1 misura).

    Per ogni riga input (1 sede), emette ``29 × 3 = 87 righe long``
    (29 anni × 3 measureType: n_pensioni / importo_medio_mensile /
    importo_annuo_complessivo). La 3a misura è stimata come
    ``n × media × 13`` (obsStatus=E + prov:wasDerivedFrom).

    Righe con n_pensioni e media_mensile entrambi NaN vengono **scartate**
    (gestione provincie nate post-1998: BAT/Fermo/Monza con celle "-" pre-2009).

    Args:
        sede_column: nome colonna sede INPS (default "sede").
        years: lista anni (default 1998-2026).
        measure_uris: dict ``{measure_short: uri_measure_property}``.
        months: moltiplicatore mensilità (default 13).

    Output: 87 righe per sede (max) con colonne:
        sede_column, anno (int), measure_short_slug, measure_uri,
        value (float), is_estimated (bool).
    """

    DEFAULT_YEARS = list(range(1998, 2027))  # 1998..2026 inclusi = 29 anni
    DEFAULT_MEASURES = ("n", "med", "ann")

    def __init__(
        self,
        measure_uris: dict[str, str],          # {measure_short: uri}
        sede_column: str = "sede",
        years: list[int] | None = None,
        months: int = 13,
    ) -> None:
        super().__init__()
        self.sede_column = sede_column
        self.years = list(years) if years else list(self.DEFAULT_YEARS)
        self.measure_uris = dict(measure_uris)
        self.months = months
        missing = set(self.DEFAULT_MEASURES) - set(self.measure_uris)
        if missing:
            raise ValueError(f"measure_uris manca chiavi: {missing}")

    def apply(self, dataset: "Dataset") -> "Dataset":
        df = dataset.to_pandas()
        if self.sede_column not in df.columns:
            raise KeyError(
                f"UnpivotINPSSerieStorica: '{self.sede_column}' non in df."
            )

        # Verifica colonne sorgente per ogni anno
        missing = []
        for year in self.years:
            for prefix in ("n_", "media_"):
                col = f"{prefix}{year}"
                if col not in df.columns:
                    missing.append(col)
        if missing:
            raise KeyError(f"UnpivotINPSSerieStorica: colonne mancanti: {missing[:5]}...")

        rows = []
        rows_skipped = 0
        for _, src in df.iterrows():
            sede = src[self.sede_column]
            for year in self.years:
                n_val = src[f"n_{year}"]
                med_val = src[f"media_{year}"]
                # Skip se entrambi NaN (province nate post-1998)
                if pd.isna(n_val) and pd.isna(med_val):
                    rows_skipped += 3  # 3 measureType che sarebbero state emesse
                    continue
                rows.append({
                    self.sede_column:     sede,
                    "anno":               year,
                    "measure_short_slug": "n",
                    "measure_uri":        self.measure_uris["n"],
                    "value":              n_val,
                    "is_estimated":       False,
                })
                rows.append({
                    self.sede_column:     sede,
                    "anno":               year,
                    "measure_short_slug": "med",
                    "measure_uri":        self.measure_uris["med"],
                    "value":              med_val,
                    "is_estimated":       False,
                })
                # 3a misura stimata
                if pd.notna(n_val) and pd.notna(med_val):
                    ann_val = float(n_val) * float(med_val) * self.months
                else:
                    ann_val = None
                rows.append({
                    self.sede_column:     sede,
                    "anno":               year,
                    "measure_short_slug": "ann",
                    "measure_uri":        self.measure_uris["ann"],
                    "value":              ann_val,
                    "is_estimated":       True,
                })
        result = pd.DataFrame(rows)

        record = StepRecord(
            name=self.name,
            params={
                "sede_column": self.sede_column,
                "years_count": len(self.years),
                "measures": sorted(self.measure_uris.keys()),
                "months": self.months,
            },
            metrics={
                "input_rows": int(len(df)),
                "output_rows": int(len(result)),
                "rows_skipped_all_nan": rows_skipped,
                "estimated_rows": int((result["is_estimated"] == True).sum()),
                "years_emitted": len(self.years),
            },
        )
        return dataset.with_data(result, step_record=record)
