"""Test per il modulo io."""
import json

import pandas as pd
import pytest

from macrorefine import Dataset
from macrorefine.history import StepRecord
from macrorefine.io import save_dataset


@pytest.fixture
def simple_dataset() -> Dataset:
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    ds = Dataset(df)
    return ds.with_data(
        df,
        step_record=StepRecord(name="MockStep", metrics={"rows": 3}),
    )


class TestSaveDatasetCSV:
    def test_save_csv(self, simple_dataset, tmp_path):
        path = tmp_path / "out.csv"
        save_dataset(simple_dataset, path)
        assert path.exists()
        loaded = pd.read_csv(path)
        assert loaded.shape == (3, 2)

    def test_save_creates_missing_directories(self, simple_dataset, tmp_path):
        path = tmp_path / "nested" / "deeper" / "out.csv"
        save_dataset(simple_dataset, path)
        assert path.exists()

    def test_returns_path(self, simple_dataset, tmp_path):
        path = tmp_path / "out.csv"
        result = save_dataset(simple_dataset, path)
        assert result == path


class TestSaveDatasetFormatDetection:
    def test_csv_extension(self, simple_dataset, tmp_path):
        save_dataset(simple_dataset, tmp_path / "out.csv")
        assert (tmp_path / "out.csv").exists()

    def test_parquet_extension(self, simple_dataset, tmp_path):
        save_dataset(simple_dataset, tmp_path / "out.parquet")
        assert (tmp_path / "out.parquet").exists()

    def test_json_extension(self, simple_dataset, tmp_path):
        path = tmp_path / "out.json"
        save_dataset(simple_dataset, path)
        assert path.exists()
        data = json.loads(path.read_text())
        assert isinstance(data, list)
        assert data[0]["a"] == 1

    def test_unsupported_extension_raises(self, simple_dataset, tmp_path):
        with pytest.raises(ValueError, match="Unsupported"):
            save_dataset(simple_dataset, tmp_path / "out.xyz")

    def test_explicit_format_overrides_extension(self, simple_dataset, tmp_path):
        # File senza estensione, formato esplicito
        path = tmp_path / "out_no_ext"
        save_dataset(simple_dataset, path, format="csv")
        assert path.exists()
        loaded = pd.read_csv(path)
        assert loaded.shape == (3, 2)


class TestSaveDatasetHistory:
    def test_save_with_history_sidecar(self, simple_dataset, tmp_path):
        path = tmp_path / "out.csv"
        save_dataset(simple_dataset, path, save_history=True)

        sidecar = tmp_path / "out.history.json"
        assert sidecar.exists()

        data = json.loads(sidecar.read_text())
        assert "steps" in data
        assert len(data["steps"]) == 1
        assert data["steps"][0]["name"] == "MockStep"
        assert data["steps"][0]["metrics"] == {"rows": 3}

    def test_save_without_history_does_not_create_sidecar(
        self, simple_dataset, tmp_path
    ):
        path = tmp_path / "out.csv"
        save_dataset(simple_dataset, path, save_history=False)
        assert not (tmp_path / "out.history.json").exists()

    def test_history_includes_metadata(self, simple_dataset, tmp_path):
        path = tmp_path / "out.csv"
        save_dataset(simple_dataset, path, save_history=True)
        data = json.loads((tmp_path / "out.history.json").read_text())
        assert "rows" in data
        assert "cols" in data
        assert data["rows"] == 3
        assert data["cols"] == 2


class TestSaveDatasetCSVOptions:
    def test_csv_kwargs_passed_through(self, simple_dataset, tmp_path):
        path = tmp_path / "out.csv"
        save_dataset(simple_dataset, path, sep=";")
        # Il file usa ; come separatore
        loaded = pd.read_csv(path, sep=";")
        assert loaded.shape == (3, 2)