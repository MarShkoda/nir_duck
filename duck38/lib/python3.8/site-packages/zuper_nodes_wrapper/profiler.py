import time
from abc import ABC, abstractmethod
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from typing import ContextManager, Dict, List, Optional, Tuple

__all__ = ['ProfilerImp', 'Profiler', 'fake_profiler']

from zuper_commons.types import ZException


@dataclass
class FinishedIteration:
    dt: float


@dataclass
class Iteration:
    tname: str
    children: "Dict[str, List[FinishedIteration]]"


class Profiler(ABC):
    @abstractmethod
    def prof(self, s: str) -> ContextManager[None]:
        yield

    @abstractmethod
    def show_stats(self, prefix: Optional[Tuple[str, ...]] = None) -> str:
        pass


class ProfilerImp(Profiler):
    context: List[Iteration]
    stats: Dict[Tuple[str, ...], List[float]]

    def __init__(self):
        self.context = [Iteration('root', defaultdict(list))]
        self.stats = defaultdict(list)
        self.t0 = time.time()

    @contextmanager
    def prof(self, s: str):
        it = Iteration(s, defaultdict(list))
        self.context.append(it)

        current_context = list(self.context)
        my_id = tuple(_.tname for _ in current_context)
        t0 = time.time()
        yield
        self.context.pop()
        dt = time.time() - t0
        s = '/'.join(my_id)
        if self.context:
            last = self.context[-1]
            last.children[s].append(FinishedIteration(dt))
        if it.children:
            explained = sum(sum(x.dt for x in _) for _ in it.children.values())
            unexplained = dt - explained
            # perc = int(100 * unexplained / dt)
            # logger.debug(f'timer: {dt:10.4f} {s}  / {unexplained:.4f} {perc}% unexp ')

            self.stats[my_id + ('self',)].append(unexplained)
        else:
            pass
            # logger.debug(f'timer: {dt:10.4f} {s}')
        self.stats[my_id].append(dt)

    def show_stats(self, prefix: Tuple[str, ...] = ('root',)) -> str:
        # logger.info(str(list(self.stats)))
        tottime = time.time() - self.t0
        lines = self.show_stats_(prefix, 1, tottime)
        if not lines:
            lines.append(f'Could not find any *completed* children for prefix {prefix}.')
            # raise ZException(msg, prefix=prefix, lines=lines,
            #                  known=list(self.stats))
        return "\n".join(lines)

    def show_stats_(self, prefix: Tuple[str, ...], ntot: int, tottime: float) -> List[str]:
        # logger.info(f'Searching while {prefix}')
        lines = []
        for k, v in self.stats.items():
            if k[:len(prefix)] != prefix:
                # logger.info(f'excluding {k}')
                continue
            if len(k) == len(prefix) + 1:
                n = len(v)
                total = sum(v)
                rn = n / ntot
                dt = total / n
                perc = 100 * total / tottime

                s = f'┌ {perc:4.1f}%   ' + k[-1] + f' {dt:6.3f}'
                if rn != 1:
                    s += f' {rn:6.1f}x'
                lines.append(s)
                for _ in self.show_stats_(prefix=k, ntot=n, tottime=total):
                    lines.append('│ ' + _)
            # else:
            #     logger.info(f'excluding {k} not child')
        # logger.info(f'lines for {prefix}: {lines}')
        return lines



class FakeProfiler(Profiler):
    @contextmanager
    def prof(self, s: str):
        yield

    def show_stats(self, prefix: Optional[Tuple[str, ...]] = None) -> str:
        return '(fake)'


fake_profiler = FakeProfiler()
