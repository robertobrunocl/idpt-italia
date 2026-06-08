"""Test ParseItalianNumbers — parsing formato italiano per CSV INPS."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from macrorefine.dataset import Dataset
from macrorefine.steps.lod import ParseItalianNumbers


class TestParseItalianNumbersBasic:
    def test_parses_thousands_and_decimals(self):
        df = pd.DataFrame({"importo": ["1.234,56", "394.676", "0,5", "1.000.000,75"]})
        ds = Dataset(df)
        out = ParseItalianNumbers(columns="importo").apply(ds)
        result = out.to_pandas()["importo"].tolist()
        assert result == [1234.56, 394676.0, 0.5, 1000000.75]

    def test_dash_becomes_nan(self):
        """`-` è il sentinella INPS per cella soppressa per privacy."""
        df = pd.DataFrame({"x": ["-", "100", "", "1.500,5"]})
        ds = Dataset(df)
        out = ParseItalianNumbers(columns="x").apply(ds)
        result = out.to_pandas()["x"].tolist()
        assert result[0] != result[0]  # NaN check
        assert result[1] == 100.0
        assert result[2] != result[2]  # NaN check (empty string)
        assert result[3] == 1500.5

    def test_strips_trailing_whitespace(self):
        """I CSV INPS terminano i valori con uno spazio: '394.676 '."""
        df = pd.DataFrame({"n": ["394.676 ", " 1.234,56 ", "- "]})
        ds = Dataset(df)
        out = ParseItalianNumbers(columns="n").apply(ds)
        result = out.to_pandas()["n"].tolist()
        assert result[0] == 394676.0
        assert result[1] == 1234.56
        assert result[2] != result[2]  # NaN

    def test_multiple_columns(self):
        df = pd.DataFrame({
            "a": ["1.000", "2.500"],
            "b": ["0,5", "1,25"],
            "c": ["txt", "other"],
        })
        ds = Dataset(df)
        out = ParseItalianNumbers(columns=["a", "b"]).apply(ds)
        df_out = out.to_pandas()
        assert df_out["a"].tolist() == [1000.0, 2500.0]
        assert df_out["b"].tolist() == [0.5, 1.25]
        # La colonna "c" è preservata invariata
        assert df_out["c"].tolist() == ["txt", "other"]


class TestParseItalianNumbersEdge:
    def test_idempotent_on_numeric_column(self):
        """Applicato a colonne già numeriche, non le altera."""
        df = pd.DataFrame({"x": [1.5, 2.0, np.nan, 100.0]})
        ds = Dataset(df)
        out = ParseItalianNumbers(columns="x").apply(ds)
        result = out.to_pandas()["x"].tolist()
        assert result[0] == 1.5
        assert result[1] == 2.0
        assert result[2] != result[2]
        assert result[3] == 100.0

    def test_preserves_pandas_na(self):
        """I NaN pandas originari restano NaN."""
        df = pd.DataFrame({"x": ["100", None, "200", np.nan]})
        ds = Dataset(df)
        out = ParseItalianNumbers(columns="x").apply(ds)
        result = out.to_pandas()["x"].tolist()
        assert result[0] == 100.0
        assert result[1] != result[1]
        assert result[2] == 200.0
        assert result[3] != result[3]

    def test_custom_na_values(self):
        """na_values configurabile."""
        df = pd.DataFrame({"x": ["100", "MISSING", "n.d.", "200"]})
        ds = Dataset(df)
        out = ParseItalianNumbers(
            columns="x", na_values=("-", "", "MISSING", "n.d.")
        ).apply(ds)
        result = out.to_pandas()["x"].tolist()
        assert result[0] == 100.0
        assert result[1] != result[1]
        assert result[2] != result[2]
        assert result[3] == 200.0

    def test_missing_column_raises(self):
        df = pd.DataFrame({"x": ["1.000"]})
        ds = Dataset(df)
        with pytest.raises(KeyError):
            ParseItalianNumbers(columns="missing").apply(ds)


class TestParseItalianNumbersHistory:
    def test_history_records_step(self):
        df = pd.DataFrame({"x": ["1.000"]})
        ds = Dataset(df)
        out = ParseItalianNumbers(columns="x").apply(ds)
        assert len(out.history) == 1
        rec = out.history[0]
        assert rec.name == "ParseItalianNumbers"
        assert rec.params["columns"] == ["x"]
