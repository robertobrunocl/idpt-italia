"""Pipeline: orchestratore di step con gestione errori configurabile."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

from macrorefine.step import PipelineStep

if TYPE_CHECKING:
    from macrorefine.dataset import Dataset

logger = logging.getLogger(__name__)

OnError = Literal["interactive", "skip", "raise"]


class Pipeline:
    """Catena ordinata di PipelineStep da applicare a un Dataset.

    Args:
        on_error: Strategia in caso di errore in uno step:
            - "interactive" (default): chiede all'utente cosa fare
            - "skip": logga l'errore e continua col prossimo step
            - "raise": rilancia l'eccezione
    """

    def __init__(self, on_error: OnError = "interactive") -> None:
        if on_error not in ("interactive", "skip", "raise"):
            raise ValueError(
                f"on_error must be one of 'interactive', 'skip', 'raise'; got {on_error!r}"
            )
        self._steps: list[PipelineStep] = []
        self._on_error: OnError = on_error

    def add(self, step: PipelineStep) -> "Pipeline":
        """Aggiunge uno step alla pipeline (fluent)."""
        if not isinstance(step, PipelineStep):
            raise TypeError(f"Expected PipelineStep, got {type(step).__name__}")
        self._steps.append(step)
        return self

    def run(self, dataset: "Dataset") -> "Dataset":
        """Esegue tutti gli step in sequenza, ritornando il Dataset finale."""
        current = dataset
        for step in self._steps:
            try:
                current = step.apply(current)
            except Exception as exc:  # noqa: BLE001
                action = self._resolve_action(step, exc)
                if action == "abort":
                    raise
                elif action == "skip":
                    logger.warning("Step %s failed and was skipped: %s", step.name, exc)
                    continue
        return current

    # ----- Gestione errori -----

    def _resolve_action(self, step: PipelineStep, exc: Exception) -> str:
        """Decide cosa fare in base a `on_error`. Ritorna 'abort' o 'skip'."""
        if self._on_error == "raise":
            return "abort"
        if self._on_error == "skip":
            return "skip"
        # interactive
        return self._prompt_user(step, exc)

    def _prompt_user(self, step: PipelineStep, exc: Exception) -> str:
        """Chiede all'utente come comportarsi davanti a un errore."""
        print(f"\n[Pipeline] Step '{step.name}' failed with error:")
        print(f"  {type(exc).__name__}: {exc}")
        while True:
            answer = input("Choose action: [continue/skip/abort]: ").strip().lower()
            if answer in ("continue", "c", "skip", "s"):
                return "skip"
            if answer in ("abort", "a"):
                return "abort"
            print("Invalid choice. Type 'continue', 'skip' or 'abort'.")

    def __repr__(self) -> str:
        names = [s.name for s in self._steps]
        return f"Pipeline(steps={names}, on_error={self._on_error!r})"