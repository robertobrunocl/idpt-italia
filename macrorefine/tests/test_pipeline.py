"""Test per Pipeline."""
import pandas as pd
import pytest
from macrorefine.dataset import Dataset
from macrorefine.pipeline import Pipeline
from macrorefine.step import PipelineStep


# Step di test riutilizzabili
class AddOneToId(PipelineStep):
    def apply(self, dataset):
        df = dataset.to_pandas().copy()
        df["id"] = df["id"] + 1
        return dataset.with_data(df, step_name=self.name)


class FailingStep(PipelineStep):
    def apply(self, dataset):
        raise ValueError("intentional failure")


class TestPipelineBasic:
    def test_empty_pipeline_returns_same_dataset(self, clean_df):
        ds = Dataset(clean_df)
        result = Pipeline().run(ds)
        assert result.to_pandas().equals(ds.to_pandas())

    def test_add_returns_self_for_chaining(self):
        p = Pipeline()
        assert p.add(AddOneToId()) is p

    def test_single_step_execution(self, clean_df):
        ds = Dataset(clean_df)
        result = Pipeline().add(AddOneToId()).run(ds)
        assert result.to_pandas()["id"].tolist() == [2, 3, 4]

    def test_multiple_steps_executed_in_order(self, clean_df):
        ds = Dataset(clean_df)
        result = Pipeline().add(AddOneToId()).add(AddOneToId()).run(ds)
        assert result.to_pandas()["id"].tolist() == [3, 4, 5]

    def test_pipeline_updates_history(self, clean_df):
        ds = Dataset(clean_df)
        result = Pipeline().add(AddOneToId()).add(AddOneToId()).run(ds)
        assert len(result.history) == 2
        assert all(r.name == "AddOneToId" for r in result.history)

    def test_original_dataset_unchanged(self, clean_df):
        ds = Dataset(clean_df)
        Pipeline().add(AddOneToId()).run(ds)
        assert ds.to_pandas()["id"].tolist() == [1, 2, 3]
        assert len(ds.history) == 0


class TestPipelineErrorHandling:
    """In caso di errore: chiede all'utente [continue/skip/abort]."""

    def test_abort_on_error(self, clean_df, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "abort")
        ds = Dataset(clean_df)

        with pytest.raises(Exception):
            Pipeline().add(FailingStep()).run(ds)

    def test_skip_on_error_continues(self, clean_df, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "skip")
        ds = Dataset(clean_df)

        result = (
            Pipeline()
            .add(FailingStep())
            .add(AddOneToId())
            .run(ds)
        )
        # FailingStep saltato, AddOneToId eseguito
        assert result.to_pandas()["id"].tolist() == [2, 3, 4]

    def test_on_error_param_overrides_prompt(self, clean_df):
        """Se passo on_error='skip', non chiede input."""
        ds = Dataset(clean_df)
        result = (
            Pipeline(on_error="skip")
            .add(FailingStep())
            .add(AddOneToId())
            .run(ds)
        )
        assert result.to_pandas()["id"].tolist() == [2, 3, 4]

    def test_on_error_raise_propagates(self, clean_df):
        ds = Dataset(clean_df)
        with pytest.raises(ValueError, match="intentional failure"):
            Pipeline(on_error="raise").add(FailingStep()).run(ds)