"""Test per il profiling."""
import pandas as pd
from macrorefine.dataset import Dataset


class TestProfile:
    def test_profile_returns_report(self, dirty_df):
        report = Dataset(dirty_df).profile()
        assert report is not None

    def test_detects_non_snake_case_columns(self, dirty_df):
        report = Dataset(dirty_df).profile()
        # Le colonne "ID", "Full Name", "EmptyCol", "City " non sono snake_case
        assert len(report.non_snake_case_columns) >= 3

    def test_detects_empty_columns(self, dirty_df):
        report = Dataset(dirty_df).profile()
        assert "EmptyCol" in report.empty_columns

    def test_detects_duplicate_rows(self, dirty_df):
        report = Dataset(dirty_df).profile()
        assert report.duplicate_rows == 1  # Charlie compare 2 volte

    def test_detects_high_null_columns(self):
        df = pd.DataFrame({
            "a": [1, 2, 3, 4, 5],
            "b": [None, None, None, None, 1],  # 80% null
        })
        report = Dataset(df).profile()
        assert "b" in report.high_null_columns

    def test_repr_is_readable(self, dirty_df):
        report = Dataset(dirty_df).profile()
        text = repr(report)
        assert isinstance(text, str)
        assert len(text) > 0