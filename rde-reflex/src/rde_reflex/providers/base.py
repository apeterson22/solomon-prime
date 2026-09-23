from __future__ import annotations

from abc import ABC, abstractmethod

from rde_reflex.models import DecisionSpec, ProviderDecision


class DecisionProvider(ABC):
    """Pluggable bounded-decision provider.

    Providers score declared candidates. They never execute the selected action.
    """

    name: str

    @abstractmethod
    async def score(self, *, state: str, decision: DecisionSpec) -> ProviderDecision:
        raise NotImplementedError
