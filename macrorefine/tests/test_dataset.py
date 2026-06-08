"""Test per Dataset."""
import pandas as pd
import pytest
from macrorefine.dataset import Dataset
from macrorefine.history import StepRecord


class TestDatasetCreation:
    def test_create_from_dataframe(self, clean_df):
        ds = Dataset(clean_df)
        assert ds.shape == (3, 3)
        assert ds.columns == ["id", "name", "value"]

    def test_history_is_empty_at_creation(self, clean_df):
        ds = Dataset(clean_df)
        assert len(ds.history) == 0


class TestDatasetIO:
    def test_from_csv(self, clean_df, tmp_path):
        path = tmp_path / "test.csv"
        clean_df.to_csv(path, index=False)

        ds = Dataset.from_csv(path)
        assert ds.shape == (3, 3)
        assert "id" in ds.columns

    def test_to_csv(self, clean_df, tmp_path):
        ds = Dataset(clean_df)
        path = tmp_path / "out.csv"
        ds.to_csv(path)

        loaded = pd.read_csv(path)
        assert loaded.shape == (3, 3)

    def test_from_parquet(self, clean_df, tmp_path):
        path = tmp_path / "test.parquet"
        clean_df.to_parquet(path)

        ds = Dataset.from_parquet(path)
        assert ds.shape == (3, 3)

    def test_to_parquet(self, clean_df, tmp_path):
        ds = Dataset(clean_df)
        path = tmp_path / "out.parquet"
        ds.to_parquet(path)
        assert path.exists()


class TestDatasetImmutability:
    def test_to_pandas_returns_copy(self, clean_df):
        """Modificare il df ottenuto da to_pandas non deve toccare il Dataset."""
        ds = Dataset(clean_df)
        df_copy = ds.to_pandas()
        df_copy["id"] = 999

        assert ds.to_pandas()["id"].tolist() == [1, 2, 3]

    def test_with_data_returns_new_dataset(self, clean_df):
        ds1 = Dataset(clean_df)
        new_df = clean_df.assign(id=[10, 20, 30])
        ds2 = ds1.with_data(new_df, step_name="ChangeIds")

        assert ds1 is not ds2
        assert ds1.to_pandas()["id"].tolist() == [1, 2, 3]
        assert ds2.to_pandas()["id"].tolist() == [10, 20, 30]

    def test_with_data_appends_to_history(self, clean_df):
        ds1 = Dataset(clean_df)
        ds2 = ds1.with_data(clean_df, step_name="StepA")
        ds3 = ds2.with_data(clean_df, step_name="StepB")

        assert len(ds1.history) == 0
        assert len(ds2.history) == 1
        assert len(ds3.history) == 2
        assert [r.name for r in ds3.history] == ["StepA", "StepB"]

    def test_with_data_accepts_step_record(self, clean_df):
        ds1 = Dataset(clean_df)
        record = StepRecord(name="X", params={"a": 1}, metrics={"b": 2})
        ds2 = ds1.with_data(clean_df, step_record=record)

        assert ds2.history[0].params == {"a": 1}
        assert ds2.history[0].metrics == {"b": 2}


class TestDatasetAccess:
    def test_columns_property(self, clean_df):
        assert Dataset(clean_df).columns == ["id", "name", "value"]

    def test_shape_property(self, clean_df):
        assert Dataset(clean_df).shape == (3, 3)

    def test_head(self, clean_df):
        head = Dataset(clean_df).head(2)
        assert isinstance(head, pd.DataFrame)
        assert len(head) == 2

    def test_repr_contains_shape(self, clean_df):
        text = repr(Dataset(clean_df))
        assert "3" in text  # rows or cols