#!/usr/bin/env python
import time
from contextlib import contextmanager

from dataclasses import dataclass, field
from typing import Dict

__all__ = ["TimeTracker"]


@dataclass
class TimeTracker:
    step: int
    total: float = 0
    phases: Dict[str, float] = field(default_factory=dict)

    @contextmanager
    def measure(self, phase_name: str):
        t0 = time.time()
        yield
        t1 = time.time()
        delta = t1 - t0
        self.phases[phase_name] = delta
        self.total += delta
