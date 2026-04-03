from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Sequence

from fx_multi_factor.data.contracts import FXBar1m

FactorComputeFn = Callable[[Sequence[FXBar1m]], list[float | None]]


@dataclass(slots=True)
class FactorSpec:
    name: str
    description: str
    inputs: tuple[str, ...]
    parameters: dict[str, float | int | str] = field(default_factory=dict)
    lookback: int = 0
    output_field: str = ""
    session_filter: tuple[str, ...] = ()
    cold_start: int = 0
    compute: FactorComputeFn = field(repr=False, compare=False, default=lambda bars: [])

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "inputs": list(self.inputs),
            "parameters": self.parameters,
            "lookback": self.lookback,
            "output_field": self.output_field or self.name,
            "session_filter": list(self.session_filter),
            "cold_start": self.cold_start,
        }

