"""MacroRefine: a simple, modular and extensible data cleaning pipeline library."""
from macrorefine.column_step import ColumnStep
from macrorefine.dataset import Dataset
from macrorefine.history import History, StepRecord
from macrorefine.io import save_dataset
from macrorefine.pipeline import Pipeline
from macrorefine.recipe import Recipe
from macrorefine.step import PipelineStep

__version__ = "0.1.0"

__all__ = [
    "Dataset",
    "Pipeline",
    "PipelineStep",
    "ColumnStep",
    "Recipe",
    "History",
    "StepRecord",
    "save_dataset",
    "__version__",
]