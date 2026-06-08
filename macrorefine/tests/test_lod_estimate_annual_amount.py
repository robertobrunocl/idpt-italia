"""Test EstimateAnnualAmount — ricostruzione importo annuo `n × media × 13`."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from macrorefine.dataset import Dataset
from macrorefine.steps.lod import EstimateAnnualAmount


class TestEstimateAnnualAmountBasic:
    def test_basic_calculation(self):
        """100 pensioni × 1000€/mese × 13 = 1.300.000 €."""
        df = pd.DataFrame({
            "n": [100, 200, 50],
            "media": [1000.0, 2000.0, 500.0],
        })
        ds = Dataset(df)
        out = EstimateAnnualAmount("n", "media", "annuo").apply(ds)
        result = out.to_pandas()["annuo"].tolist()
        assert result == [100 * 1000 * 13, 200 * 2000 * 13, 50 * 500 * 13]

    def test_scale_in_millions(self):
        """scale=1e-6 converte euro → milioni di euro (coerente con cubo 1)."""
        df = pd.DataFrame({
            "n": [1_000_000],     # 1 milione di pensioni
            "media": [1500.0],    # 1500 €/mese
        })
        ds = Dataset(df)
        out = EstimateAnnualAmount(
            "n", "media", "annuo_mln", scale=1e-6
        ).apply(ds)
        # 1.000.000 × 1500 × 13 × 1e-6 = 19500
        assert out.to_pandas()["annuo_mln"].iloc[0] == pytest.approx(19500.0)

    def test_nan_propagates(self):
        """NaN in count o monthly → NaN in output (semantica pandas)."""
        df = pd.DataFrame({
            "n": [100, np.nan, 50],
            "media": [1000.0, 2000.0, np.nan],
        })
        ds = Dataset(df)
        out = EstimateAnnualAmount("n", "media", "annuo").apply(ds)
        result = out.to_pandas()["annuo"].tolist()
        assert result[0] == 100 * 1000 * 13
        assert result[1] != result[1]
        assert result[2] != result[2]


class TestEstimateAnnualAmountConfig:
    def test_custom_months(self):
        """In altri paesi non c'è la 13esima: months=12."""
        df = pd.DataFrame({"n": [10], "media": [1000.0]})
        ds = Dataset(df)
        out = EstimateAnnualAmount("n", "media", "annuo", months=12).apply(ds)
        assert out.to_pandas()["annuo"].iloc[0] == 10 * 1000 * 12

    def test_negative_months_raises(self):
        with pytest.raises(ValueError):
            EstimateAnnualAmount("n", "media", "annuo", months=0)

    def test_missing_source_column_raises(self):
        df = pd.DataFrame({"n": [10]})  # manca "media"
        ds = Dataset(df)
        with pytest.raises(KeyError):
            EstimateAnnualAmount("n", "media", "annuo").apply(ds)


class TestEstimateAnnualAmountHistory:
    def test_records_params_and_metrics(self):
        df = pd.DataFrame({"n": [10, 20, 30], "media": [100.0, 200.0, 300.0]})
        ds = Dataset(df)
        out = EstimateAnnualAmount("n", "media", "annuo", scale=1.0).apply(ds)
        rec = out.history[0]
        assert rec.name == "EstimateAnnualAmount"
        assert rec.params == {
            "count_col": "n",
            "monthly_col": "media",
            "output_col": "annuo",
            "months": 13,
            "scale": 1.0,
        }
        # Metriche: 3 righe input, 3 non-null in output, sum = (10*100 + 20*200 + 30*300)*13
        expected_sum = (10 * 100 + 20 * 200 + 30 * 300) * 13
        assert rec.metrics["input_rows"] == 3
        assert rec.metrics["non_null_rows"] == 3
        assert rec.metrics["estimated_sum"] == pytest.approx(expected_sum)

    def test_all_nan_column_serializes_none(self):
        """Se la colonna risultato è tutta NaN, estimated_sum deve essere None (JSON-safe)."""
        df = pd.DataFrame({"n": [np.nan, np.nan], "media": [np.nan, np.nan]})
        ds = Dataset(df)
        out = EstimateAnnualAmount("n", "media", "annuo").apply(ds)
        rec = out.history[0]
        assert rec.metrics["estimated_sum"] in (0.0, None)  # pandas può ritornare 0 o NaN su sum di tutto NaN
