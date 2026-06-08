"""Test per gli step built-in."""
import numpy as np
import pandas as pd
import pytest
from macrorefine.dataset import Dataset
from macrorefine.steps import (
    NormalizeColumnNames,
    DropEmptyColumns,
    DropDuplicateRows,
    DropColumns,
    FillMissing,
    RenameColumns,
    CastTypes,
    ParseDates,
)

from macrorefine.steps import AddNormalizedKey, FilterRows, LeftJoinEnrich



class TestNormalizeColumnNames:
    def test_uppercase_to_snake_case(self):
        df = pd.DataFrame({"FullName": [1], "ID": [2]})
        result = NormalizeColumnNames().apply(Dataset(df))
        assert result.columns == ["full_name", "id"]

    def test_spaces_to_underscores(self):
        df = pd.DataFrame({"Full Name": [1], "City ": [2]})
        result = NormalizeColumnNames().apply(Dataset(df))
        assert result.columns == ["full_name", "city"]

    def test_special_chars_removed(self):
        df = pd.DataFrame({"name@home": [1], "price($)": [2]})
        result = NormalizeColumnNames().apply(Dataset(df))
        assert result.columns == ["name_home", "price"]

    def test_already_snake_case_unchanged(self):
        df = pd.DataFrame({"full_name": [1], "id": [2]})
        result = NormalizeColumnNames().apply(Dataset(df))
        assert result.columns == ["full_name", "id"]

    def test_history_recorded(self):
        df = pd.DataFrame({"a": [1]})
        result = RenameColumns(mapping={"a": "x"}).apply(Dataset(df))
        assert len(result.history) == 1
        assert result.history[0].name == "RenameColumns"
        assert result.history[0].params["mapping"] == {"a": "x"}

    def test_rename_single_column(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        result = RenameColumns(mapping={"a": "alpha"}).apply(Dataset(df))
        assert result.columns == ["alpha", "b"]

    def test_rename_multiple_columns(self):
        df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
        result = RenameColumns(mapping={"a": "alpha", "c": "gamma"}).apply(Dataset(df))
        assert result.columns == ["alpha", "b", "gamma"]

    def test_rename_missing_column_raises(self):
        df = pd.DataFrame({"a": [1]})
        with pytest.raises(KeyError):
            RenameColumns(mapping={"missing": "x"}).apply(Dataset(df))

    def test_rename_to_existing_column_raises(self):
        """Non si può rinominare in un nome già presente (eviterebbe duplicati)."""
        df = pd.DataFrame({"a": [1], "b": [2]})
        with pytest.raises(ValueError):
            RenameColumns(mapping={"a": "b"}).apply(Dataset(df))



class TestDropEmptyColumns:
    def test_drops_fully_empty_columns(self):
        df = pd.DataFrame({
            "a": [1, 2, 3],
            "empty": [None, None, None],
            "b": [4, 5, 6],
        })
        result = DropEmptyColumns().apply(Dataset(df))
        assert result.columns == ["a", "b"]

    def test_keeps_non_empty(self):
        df = pd.DataFrame({"a": [1, None, 3]})
        result = DropEmptyColumns().apply(Dataset(df))
        assert result.columns == ["a"]


class TestDropDuplicateRows:
    def test_drops_duplicates(self):
        df = pd.DataFrame({"a": [1, 2, 2, 3], "b": [10, 20, 20, 30]})
        result = DropDuplicateRows().apply(Dataset(df))
        assert result.shape == (3, 2)

    def test_no_duplicates_no_change(self):
        df = pd.DataFrame({"a": [1, 2, 3]})
        result = DropDuplicateRows().apply(Dataset(df))
        assert result.shape == (3, 1)


class TestDropColumns:
    def test_drop_single_column(self):
        df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
        result = DropColumns(columns=["b"]).apply(Dataset(df))
        assert result.columns == ["a", "c"]

    def test_drop_multiple_columns(self):
        df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
        result = DropColumns(columns=["a", "c"]).apply(Dataset(df))
        assert result.columns == ["b"]

    def test_drop_missing_column_raises(self):
        df = pd.DataFrame({"a": [1]})
        with pytest.raises(KeyError):
            DropColumns(columns=["x"]).apply(Dataset(df))


class TestFillMissing:
    def test_fill_with_constant(self):
        df = pd.DataFrame({"a": [1.0, None, 3.0]})
        result = FillMissing(columns=["a"], strategy="constant", value=0).apply(Dataset(df))
        assert result.to_pandas()["a"].tolist() == [1.0, 0.0, 3.0]

    def test_fill_with_mean(self):
        df = pd.DataFrame({"a": [1.0, None, 3.0]})
        result = FillMissing(columns=["a"], strategy="mean").apply(Dataset(df))
        assert result.to_pandas()["a"].tolist() == [1.0, 2.0, 3.0]

    def test_fill_with_median(self):
        df = pd.DataFrame({"a": [1.0, None, 3.0, 5.0]})
        result = FillMissing(columns=["a"], strategy="median").apply(Dataset(df))
        filled = result.to_pandas()["a"].tolist()
        assert filled[1] == 3.0  # median di [1, 3, 5]

    def test_invalid_strategy_raises(self):
        df = pd.DataFrame({"a": [1.0, None]})
        with pytest.raises(ValueError):
            FillMissing(columns=["a"], strategy="bogus").apply(Dataset(df))


class TestCastTypes:
    def test_cast_int_to_float(self):
        df = pd.DataFrame({"a": [1, 2, 3]})
        result = CastTypes(mapping={"a": "float"}).apply(Dataset(df))
        assert result.to_pandas()["a"].dtype.kind == "f"

    def test_cast_string_numbers_to_int(self):
        df = pd.DataFrame({"a": ["1", "2", "3"]})
        result = CastTypes(mapping={"a": "int"}).apply(Dataset(df))
        assert result.to_pandas()["a"].tolist() == [1, 2, 3]

    def test_cast_multiple_columns(self):
        df = pd.DataFrame({"a": ["1", "2"], "b": [1.1, 2.2]})
        result = CastTypes(mapping={"a": "int", "b": "str"}).apply(Dataset(df))
        out = result.to_pandas()
        assert out["a"].tolist() == [1, 2]
        assert out["b"].tolist() == ["1.1", "2.2"]

    def test_cast_missing_column_raises(self):
        df = pd.DataFrame({"a": [1]})
        with pytest.raises(KeyError):
            CastTypes(mapping={"missing": "int"}).apply(Dataset(df))

    def test_cast_invalid_value_raises_by_default(self):
        df = pd.DataFrame({"a": ["1", "not_a_number", "3"]})
        with pytest.raises(Exception):
            CastTypes(mapping={"a": "int"}).apply(Dataset(df))

    def test_cast_with_errors_coerce(self):
        """Con errors='coerce' i valori non convertibili diventano NaN."""
        df = pd.DataFrame({"a": ["1", "bad", "3"]})
        result = CastTypes(mapping={"a": "float"}, errors="coerce").apply(Dataset(df))
        out = result.to_pandas()["a"]
        assert out[0] == 1.0
        assert pd.isna(out[1])
        assert out[2] == 3.0

    def test_history_recorded(self):
        df = pd.DataFrame({"a": [1]})
        result = CastTypes(mapping={"a": "float"}).apply(Dataset(df))
        assert result.history[0].name == "CastTypes"
        assert result.history[0].params["mapping"] == {"a": "float"}


class TestParseDates:
    def test_parse_iso_format(self):
        df = pd.DataFrame({"d": ["2024-01-15", "2024-02-20"]})
        result = ParseDates(columns=["d"]).apply(Dataset(df))
        out = result.to_pandas()["d"]
        assert pd.api.types.is_datetime64_any_dtype(out)
        assert out[0].year == 2024 and out[0].month == 1

    def test_parse_with_format(self):
        df = pd.DataFrame({"d": ["15/01/2024", "20/02/2024"]})
        result = ParseDates(columns=["d"], format="%d/%m/%Y").apply(Dataset(df))
        out = result.to_pandas()["d"]
        assert out[0].day == 15 and out[0].month == 1

    def test_parse_multiple_columns(self):
        df = pd.DataFrame({
            "start": ["2024-01-01", "2024-02-01"],
            "end": ["2024-01-15", "2024-02-15"],
        })
        result = ParseDates(columns=["start", "end"]).apply(Dataset(df))
        out = result.to_pandas()
        assert pd.api.types.is_datetime64_any_dtype(out["start"])
        assert pd.api.types.is_datetime64_any_dtype(out["end"])

    def test_parse_invalid_with_coerce(self):
        df = pd.DataFrame({"d": ["2024-01-01", "not_a_date", "2024-02-01"]})
        result = ParseDates(columns=["d"], errors="coerce").apply(Dataset(df))
        out = result.to_pandas()["d"]
        assert pd.notna(out[0])
        assert pd.isna(out[1])
        assert pd.notna(out[2])

    def test_parse_invalid_with_raise(self):
        df = pd.DataFrame({"d": ["2024-01-01", "not_a_date"]})
        with pytest.raises(Exception):
            ParseDates(columns=["d"], errors="raise").apply(Dataset(df))

    def test_missing_column_raises(self):
        df = pd.DataFrame({"a": ["2024-01-01"]})
        with pytest.raises(KeyError):
            ParseDates(columns=["missing"]).apply(Dataset(df))

    def test_accepts_single_column_as_string(self):
        df = pd.DataFrame({"d": ["2024-01-01"]})
        result = ParseDates(columns="d").apply(Dataset(df))
        assert pd.api.types.is_datetime64_any_dtype(result.to_pandas()["d"])

    def test_history_recorded(self):
        df = pd.DataFrame({"d": ["2024-01-01"]})
        result = ParseDates(columns=["d"], format="%Y-%m-%d").apply(Dataset(df))
        assert result.history[0].name == "ParseDates"
        assert result.history[0].params["columns"] == ["d"]
        assert result.history[0].params["format"] == "%Y-%m-%d"


class TestAddNormalizedKey:
    def test_adds_new_column_preserving_original(self):
        df = pd.DataFrame({"comune": ["Roma", "Milano"]})
        result = AddNormalizedKey(source="comune", target="_key").apply(Dataset(df))
        out = result.to_pandas()
        assert out["comune"].tolist() == ["Roma", "Milano"]
        assert out["_key"].tolist() == ["roma", "milano"]

    def test_normalizes_accents(self):
        df = pd.DataFrame({"c": ["Forlì", "Cesenà", "Münich"]})
        result = AddNormalizedKey(source="c", target="_k").apply(Dataset(df))
        assert result.to_pandas()["_k"].tolist() == ["forli", "cesena", "munich"]

    def test_normalizes_whitespace(self):
        df = pd.DataFrame({"c": ["  Roma  ", "Reggio   Emilia"]})
        result = AddNormalizedKey(source="c", target="_k").apply(Dataset(df))
        assert result.to_pandas()["_k"].tolist() == ["roma", "reggio emilia"]

    def test_normalizes_curly_apostrophes(self):
        df = pd.DataFrame({"c": ["Sant\u2019Angelo", "L'Aquila"]})
        result = AddNormalizedKey(source="c", target="_k").apply(Dataset(df))
        out = result.to_pandas()["_k"].tolist()
        assert out == ["sant'angelo", "l'aquila"]

    def test_handles_none(self):
        df = pd.DataFrame({"c": ["Roma", None]})
        result = AddNormalizedKey(source="c", target="_k").apply(Dataset(df))
        out = result.to_pandas()["_k"].tolist()
        assert out[0] == "roma"
        assert out[1] is None or pd.isna(out[1])

    def test_missing_source_raises(self):
        df = pd.DataFrame({"x": [1]})
        with pytest.raises(KeyError):
            AddNormalizedKey(source="missing", target="_k").apply(Dataset(df))

    def test_history_recorded(self):
        df = pd.DataFrame({"a": ["X"]})
        result = AddNormalizedKey(source="a", target="_a_key").apply(Dataset(df))
        assert result.history[0].name == "AddNormalizedKey"
        assert result.history[0].params == {"source": "a", "target": "_a_key"}


class TestFilterRows:
    def test_basic_filter(self):
        df = pd.DataFrame({"a": [1, 2, 3, 4]})
        result = FilterRows(predicate=lambda d: d["a"] > 2).apply(Dataset(df))
        assert result.to_pandas()["a"].tolist() == [3, 4]

    def test_empty_result(self):
        df = pd.DataFrame({"a": [1, 2, 3]})
        result = FilterRows(predicate=lambda d: d["a"] > 100).apply(Dataset(df))
        assert result.shape == (0, 1)

    def test_metrics(self):
        df = pd.DataFrame({"a": [1, 2, 3, 4]})
        result = FilterRows(predicate=lambda d: d["a"] > 2).apply(Dataset(df))
        m = result.history[0].metrics
        assert m["rows_before"] == 4
        assert m["rows_after"] == 2
        assert m["rows_removed"] == 2


class TestLeftJoinEnrich:
    def test_simple_join(self):
        left = Dataset(pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]}))
        right = Dataset(pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]}))
        result = LeftJoinEnrich(
            other=right, left_on="id", right_on="id", columns=["value"]
        ).apply(left)
        assert result.to_pandas()["value"].tolist() == [10, 20, 30]

    def test_composite_key(self):
        left = Dataset(pd.DataFrame({
            "comune": ["Roma", "Castelnuovo"],
            "prov": ["RM", "PD"],
        }))
        right = Dataset(pd.DataFrame({
            "label": ["Roma", "Castelnuovo", "Castelnuovo"],
            "sigla": ["RM", "PD", "VR"],
            "id_comune": [1, 2, 3],
        }))
        result = LeftJoinEnrich(
            other=right,
            left_on=["comune", "prov"],
            right_on=["label", "sigla"],
            columns=["id_comune"],
        ).apply(left)
        assert result.to_pandas()["id_comune"].tolist() == [1, 2]

    def test_no_match_produces_nan(self):
        left = Dataset(pd.DataFrame({"id": [1, 2, 999]}))
        right = Dataset(pd.DataFrame({"id": [1, 2], "value": [10, 20]}))
        result = LeftJoinEnrich(
            other=right, left_on="id", right_on="id", columns=["value"]
        ).apply(left)
        out = result.to_pandas()["value"].tolist()
        assert out[0] == 10 and out[1] == 20
        assert pd.isna(out[2])

    def test_metrics_match_unmatch(self):
        left = Dataset(pd.DataFrame({"id": [1, 2, 999]}))
        right = Dataset(pd.DataFrame({"id": [1, 2], "value": [10, 20]}))
        result = LeftJoinEnrich(
            other=right, left_on="id", right_on="id", columns=["value"]
        ).apply(left)
        m = result.history[0].metrics
        assert m["matched"] == 2
        assert m["unmatched"] == 1

    def test_left_on_right_on_length_mismatch(self):
        right = Dataset(pd.DataFrame({"a": [1]}))
        with pytest.raises(ValueError):
            LeftJoinEnrich(other=right, left_on=["a", "b"], right_on=["a"], columns=[])

    def test_missing_columns_raise(self):
        left = Dataset(pd.DataFrame({"id": [1]}))
        right = Dataset(pd.DataFrame({"id": [1], "value": [10]}))
        with pytest.raises(KeyError):
            LeftJoinEnrich(
                other=right, left_on="missing", right_on="id", columns=["value"]
            ).apply(left)
        with pytest.raises(KeyError):
            LeftJoinEnrich(
                other=right, left_on="id", right_on="id", columns=["nope"]
            ).apply(left)