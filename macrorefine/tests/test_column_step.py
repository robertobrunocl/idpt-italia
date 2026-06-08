"""Test per ColumnStep."""
import pandas as pd
import pytest

from macrorefine import ColumnStep, Dataset


class TestColumnStepBasics:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            ColumnStep(columns=["a"])

    def test_subclass_must_implement_transform_column(self):
        class Incomplete(ColumnStep):
            pass

        with pytest.raises(TypeError):
            Incomplete(columns=["a"])

    def test_accepts_single_column_as_string(self):
        class MyStep(ColumnStep):
            def transform_column(self, series, column_name):
                return series

        assert MyStep(columns="a").columns == ["a"]

    def test_accepts_list_of_columns(self):
        class MyStep(ColumnStep):
            def transform_column(self, series, column_name):
                return series

        assert MyStep(columns=["a", "b"]).columns == ["a", "b"]


class TestColumnStepApply:
    def test_transforms_single_column(self):
        class DoubleValue(ColumnStep):
            def transform_column(self, series, column_name):
                return series * 2

        df = pd.DataFrame({"a": [1, 2, 3], "b": [10, 20, 30]})
        result = DoubleValue(columns="a").apply(Dataset(df))

        assert result.to_pandas()["a"].tolist() == [2, 4, 6]
        assert result.to_pandas()["b"].tolist() == [10, 20, 30]

    def test_transforms_multiple_columns(self):
        class DoubleValue(ColumnStep):
            def transform_column(self, series, column_name):
                return series * 2

        df = pd.DataFrame({"a": [1, 2], "b": [10, 20], "c": [100, 200]})
        result = DoubleValue(columns=["a", "b"]).apply(Dataset(df))

        assert result.to_pandas()["a"].tolist() == [2, 4]
        assert result.to_pandas()["b"].tolist() == [20, 40]
        assert result.to_pandas()["c"].tolist() == [100, 200]

    def test_receives_column_name(self):
        """transform_column riceve sia la series sia il nome."""
        seen_names: list[str] = []

        class Recorder(ColumnStep):
            def transform_column(self, series, column_name):
                seen_names.append(column_name)
                return series

        df = pd.DataFrame({"x": [1], "y": [2]})
        Recorder(columns=["x", "y"]).apply(Dataset(df))
        assert seen_names == ["x", "y"]

    def test_missing_column_raises(self):
        class NoOp(ColumnStep):
            def transform_column(self, series, column_name):
                return series

        df = pd.DataFrame({"a": [1]})
        with pytest.raises(KeyError):
            NoOp(columns=["missing"]).apply(Dataset(df))

    def test_history_recorded(self):
        class NoOp(ColumnStep):
            def transform_column(self, series, column_name):
                return series

        df = pd.DataFrame({"a": [1]})
        result = NoOp(columns=["a"]).apply(Dataset(df))

        assert len(result.history) == 1
        assert result.history[0].name == "NoOp"
        assert result.history[0].params["columns"] == ["a"]

    def test_immutability(self):
        class AddHundred(ColumnStep):
            def transform_column(self, series, column_name):
                return series + 100

        df = pd.DataFrame({"a": [1, 2]})
        ds = Dataset(df)
        result = AddHundred(columns="a").apply(ds)

        assert ds.to_pandas()["a"].tolist() == [1, 2]
        assert result.to_pandas()["a"].tolist() == [101, 102]


class TestColumnStepRealWorldExamples:
    """Test di casi d'uso realistici."""

    def test_uppercase_multiple_cols(self):
        class Uppercase(ColumnStep):
            def transform_column(self, series, column_name):
                return series.str.upper()

        df = pd.DataFrame({
            "name": ["alice", "bob"],
            "city": ["rome", "milan"],
            "id": [1, 2],
        })
        result = Uppercase(columns=["name", "city"]).apply(Dataset(df))

        assert result.to_pandas()["name"].tolist() == ["ALICE", "BOB"]
        assert result.to_pandas()["city"].tolist() == ["ROME", "MILAN"]
        assert result.to_pandas()["id"].tolist() == [1, 2]

    def test_strip_accents(self):
        import unicodedata

        class StripAccents(ColumnStep):
            def transform_column(self, series, column_name):
                return series.apply(
                    lambda x: unicodedata.normalize("NFKD", str(x))
                    .encode("ascii", "ignore")
                    .decode()
                )

        df = pd.DataFrame({"city": ["Café", "Roma", "Münich"]})
        result = StripAccents(columns="city").apply(Dataset(df))

        assert result.to_pandas()["city"].tolist() == ["Cafe", "Roma", "Munich"]