class ContractValidationError(ValueError):
    """Base error for invalid runtime-contract data."""


class InvalidPlanError(ContractValidationError):
    """Raised when an execution plan violates contract invariants."""


class InvalidResultError(ContractValidationError):
    """Raised when an execution result violates contract invariants."""
