from __future__ import annotations


class ProMaxRuntimeError(Exception):
    """Base class for deterministic ProMax runtime failures."""


class CanonicalJSONError(ProMaxRuntimeError, ValueError):
    """Raised when a value cannot be represented as canonical JSON."""


class JSONDocumentError(ProMaxRuntimeError, ValueError):
    """Raised when a JSON or JSONL document violates the runtime contract."""


class RunBindingError(ProMaxRuntimeError, ValueError):
    """Raised when a run is not bound to one immutable v8 request identity."""


class PhaseHistoryError(ProMaxRuntimeError, ValueError):
    """Raised when an append-only phase history is invalid."""


class PhaseTransitionError(PhaseHistoryError):
    """Raised when a phase transition violates P0-P11 ordering."""


class PhaseParentHashError(PhaseHistoryError):
    """Raised when a phase is not linked to the current valid parent phase."""


class PhaseReplayError(PhaseHistoryError):
    """Raised when a previously consumed phase event is replayed."""


class StaleArtifactError(PhaseHistoryError):
    """Raised when an event reads an invalidated phase or artifact generation."""


class PhaseCASMismatch(PhaseHistoryError):
    """Raised when an append caller's expected chain head is stale."""


class PhaseLockBusy(PhaseHistoryError):
    """Raised when another process holds the phase-event sidecar lock."""
