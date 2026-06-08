"""Test AggregateMEFRedditiByProvincia — aggregazione comuni → province + unpivot."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from macrorefine.dataset import Dataset
from macrorefine.steps.lod import AggregateMEFRedditiByProvincia
from macrorefine.steps.lod.aggregate import DEFAULT_MEF_VOCI_COLUMNS


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEF_CSV = PROJECT_ROOT / "data" / "mef_redditi_irpef_comune_2024_v1.csv"

SAMPLE_VOCI_URI = {
    "v2": "https://example.org/idpt/voce-redd-lavoro-dipendente",
    "v4": "https://example.org/idpt/voce-redd-lavoro-autonomo",
    "v5": "https://example.org/idpt/voce-redd-imprenditore-ord",
    "v6": "https://example.org/idpt/voce-redd-imprenditore-sempl",
    "v7": "https://example.org/idpt/voce-redd-partecipazione",
}


def _make_synthetic_df():
    """5 comuni in 2 sigle + 1 sentinella Sigla=0."""
    rows = []
    voci = list(DEFAULT_MEF_VOCI_COLUMNS.items())
    for comune, sigla, base in [
        ("Torino",       "TO", 100),
        ("Moncalieri",   "TO",  50),
        ("Roma",         "RM", 500),
        ("Aprilia",      "LT", 200),
        ("Latina",       "LT", 150),
        ("Sentinella",   "0",  999),  # da escludere
    ]:
        row = {"Comune": comune, "Sigla Provincia": sigla}
        for short, (freq_col, amm_col) in voci:
            row[freq_col] = str(base)
            row[amm_col] = str(base * 1000)
        rows.append(row)
    return pd.DataFrame(rows)


class TestAggregateMEFBasic:
    def test_drops_sentinel_and_aggregates(self):
        df = _make_synthetic_df()
        out = AggregateMEFRedditiByProvincia(
            voci_uri=SAMPLE_VOCI_URI,
        ).apply(Dataset(df)).to_pandas()

        # 3 sigle valide (TO, RM, LT) × 5 voci = 15 righe
        assert len(out) == 15
        assert set(out["Sigla Provincia"].unique()) == {"TO", "RM", "LT"}

    def test_count_aggregation_correct(self):
        df = _make_synthetic_df()
        out = AggregateMEFRedditiByProvincia(
            voci_uri=SAMPLE_VOCI_URI,
        ).apply(Dataset(df)).to_pandas()

        # TO ha 2 comuni (Torino 100 + Moncalieri 50) = 150 per ogni voce
        to_rows = out[out["Sigla Provincia"] == "TO"]
        assert all(to_rows["frequenza_dichiaranti"] == 150)
        assert all(to_rows["ammontare_totale"] == 150000)

        # LT ha 2 comuni (Aprilia 200 + Latina 150) = 350
        lt_rows = out[out["Sigla Provincia"] == "LT"]
        assert all(lt_rows["frequenza_dichiaranti"] == 350)

    def test_empty_strings_become_zero(self):
        df = _make_synthetic_df()
        # Sostituisco alcuni valori con stringa vuota
        first_v2_freq = DEFAULT_MEF_VOCI_COLUMNS["v2"][0]
        df.loc[0, first_v2_freq] = ""  # Torino frequency v2 = ""
        out = AggregateMEFRedditiByProvincia(
            voci_uri=SAMPLE_VOCI_URI,
        ).apply(Dataset(df)).to_pandas()

        # TO v2 frequenza = 50 (Moncalieri) + 0 (Torino stringa vuota → 0)
        to_v2 = out[(out["Sigla Provincia"] == "TO") & (out["voce_short"] == "v2")].iloc[0]
        assert to_v2["frequenza_dichiaranti"] == 50

    def test_voce_uri_assigned(self):
        df = _make_synthetic_df()
        out = AggregateMEFRedditiByProvincia(
            voci_uri=SAMPLE_VOCI_URI,
        ).apply(Dataset(df)).to_pandas()

        # Per ogni riga, voce_uri deve corrispondere alla voce_short
        for _, row in out.iterrows():
            assert row["voce_uri"] == SAMPLE_VOCI_URI[row["voce_short"]]


class TestAggregateMEFConfig:
    def test_missing_voci_uri_raises(self):
        """Se voci_uri non copre tutte le voci_columns → ValueError."""
        with pytest.raises(ValueError, match="non ha URI per"):
            AggregateMEFRedditiByProvincia(
                voci_uri={"v2": "x"},  # mancano v4/v5/v6/v7
            )

    def test_missing_csv_column_raises(self):
        df = pd.DataFrame({"Sigla Provincia": ["TO"]})  # mancano colonne reddito
        with pytest.raises(KeyError):
            AggregateMEFRedditiByProvincia(
                voci_uri=SAMPLE_VOCI_URI,
            ).apply(Dataset(df))

    def test_custom_sentinel(self):
        df = _make_synthetic_df()
        # Custom sentinella = "RM" → Roma esclusa
        out = AggregateMEFRedditiByProvincia(
            voci_uri=SAMPLE_VOCI_URI,
            sentinel_sigla="RM",
        ).apply(Dataset(df)).to_pandas()
        assert "RM" not in out["Sigla Provincia"].unique()


class TestAggregateMEFHistory:
    def test_records_metrics(self):
        df = _make_synthetic_df()
        out_ds = AggregateMEFRedditiByProvincia(
            voci_uri=SAMPLE_VOCI_URI,
        ).apply(Dataset(df))
        rec = out_ds.history[0]
        assert rec.name == "AggregateMEFRedditiByProvincia"
        assert rec.metrics["input_rows"] == 6
        assert rec.metrics["output_rows"] == 15
        assert rec.metrics["rows_dropped_sentinel"] == 1
        assert rec.metrics["aggregated_provinces"] == 3
        assert rec.metrics["voci_emitted"] == 5


@pytest.mark.skipif(not MEF_CSV.exists(), reason="CSV MEF non trovato")
class TestAggregateMEFEndToEnd:
    """End-to-end sul CSV MEF reale (7897 comuni → 535 righe)."""

    def test_real_csv_yields_535_rows(self):
        df = pd.read_csv(
            MEF_CSV, sep=";", dtype=str, encoding="utf-8",
            keep_default_na=False,
        )
        assert df.shape[0] == 7897, f"Atteso 7897 comuni, trovati {df.shape[0]}"

        out_ds = AggregateMEFRedditiByProvincia(
            voci_uri=SAMPLE_VOCI_URI,
        ).apply(Dataset(df))
        out = out_ds.to_pandas()

        # 107 sigle valide × 5 voci = 535
        assert len(out) == 535, f"Atteso 535 righe long, trovate {len(out)}"
        # 107 province distinte
        assert out["Sigla Provincia"].nunique() == 107
        # 5 voci uniche
        assert sorted(out["voce_short"].unique()) == ["v2", "v4", "v5", "v6", "v7"]

        rec = out_ds.history[0]
        assert rec.metrics["rows_dropped_sentinel"] == 1
        assert rec.metrics["aggregated_provinces"] == 107
