"""History e StepRecord: audit trail immutabile delle operazioni applicate a un Dataset."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator


@dataclass(frozen=True)
class StepRecord:
    """Record immutabile di un singolo step applicato.

    Attributes:
        name: Nome dello step (di solito il nome della classe).
        params: Parametri con cui lo step è stato configurato.
        metrics: Metriche calcolate durante l'esecuzione (es. righe rimosse).
    """
    name: str
    params: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)


class History:
    """Lista immutabile di StepRecord.

    Ogni operazione di append ritorna una nuova History, lasciando
    invariata l'istanza originale.
    """

    def __init__(self, records: tuple[StepRecord, ...] = ()) -> None:
        self._records: tuple[StepRecord, ...] = tuple(records)

    def append(self, record: StepRecord) -> "History":
        """Ritorna una nuova History con il record aggiunto in coda."""
        return History(self._records + (record,))

    def __len__(self) -> int:
        return len(self._records)

    def __iter__(self) -> Iterator[StepRecord]:
        return iter(self._records)

    def __getitem__(self, index: int) -> StepRecord:
        return self._records[index]

    def __repr__(self) -> str:
        if not self._records:
            return "History(empty)"
        lines = ["History:"]
        for i, r in enumerate(self._records, 1):
            lines.append(f"  {i}. {r.name}  params={r.params}  metrics={r.metrics}")
        return "\n".join(lines)