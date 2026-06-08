"""Fixture comuni per i test di macrorefine."""
import pandas as pd
import pytest


@pytest.fixture
def dirty_df() -> pd.DataFrame:
    """DataFrame con vari problemi tipici: nomi sporchi, colonna vuota, duplicati, null."""
    return pd.DataFrame({
        "ID": [1, 2, 3, 3, 4],
        "Full Name": ["Alice", "Bob", "Charlie", "Charlie", "Diana"],
        "Age": [30, None, 25, 25, 40],
        "EmptyCol": [None, None, None, None, None],
        "City ": ["Rome", "Milan", "Naples", "Naples", "Turin"],
    })


@pytest.fixture
def clean_df() -> pd.DataFrame:
    """DataFrame pulito di partenza."""
    return pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["a", "b", "c"],
        "value": [10.0, 20.0, 30.0],
    })