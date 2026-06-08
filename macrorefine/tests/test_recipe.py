"""Test per Recipe."""
import pandas as pd
import pytest
from macrorefine.dataset import Dataset
from macrorefine.pipeline import Pipeline
from macrorefine.recipe import Recipe
from macrorefine.steps import NormalizeColumnNames, DropEmptyColumns


class TestRecipe:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            Recipe()

    def test_subclass_must_implement_build(self):
        class Incomplete(Recipe):
            pass
        with pytest.raises(TypeError):
            Incomplete()

    def test_recipe_applies_pipeline(self):
        class MyRecipe(Recipe):
            def build(self) -> Pipeline:
                return Pipeline().add(NormalizeColumnNames()).add(DropEmptyColumns())

        df = pd.DataFrame({"FullName": [1, 2], "Empty": [None, None]})
        result = MyRecipe().apply(Dataset(df))
        assert result.columns == ["full_name"]

    def test_recipe_with_parameters(self):
        class ParamRecipe(Recipe):
            def __init__(self, drop_empty: bool):
                self.drop_empty = drop_empty

            def build(self) -> Pipeline:
                p = Pipeline().add(NormalizeColumnNames())
                if self.drop_empty:
                    p.add(DropEmptyColumns())
                return p

        df = pd.DataFrame({"X": [1], "Empty": [None]})

        kept = ParamRecipe(drop_empty=False).apply(Dataset(df))
        assert kept.columns == ["x", "empty"]

        dropped = ParamRecipe(drop_empty=True).apply(Dataset(df))
        assert dropped.columns == ["x"]