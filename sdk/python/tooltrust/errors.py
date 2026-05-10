from .tool import RiskClass, AuthorityLevel


class ToolTrustError(Exception):
    """Base error for Tool Trust SDK."""
    pass


class AuthorizationError(ToolTrustError):
    """Tool call not authorized — authority level too low."""
    def __init__(self, current: AuthorityLevel, required: AuthorityLevel, message: str):
        self.current = current
        self.required = required
        super().__init__(message)


class RiskClassBlockedError(ToolTrustError):
    """Risk class blocked in current mode."""
    def __init__(self, risk_class: RiskClass, required_mode: str, message: str):
        self.risk_class = risk_class
        self.required_mode = required_mode
        super().__init__(message)


class QuotaExceededError(ToolTrustError):
    """SCU quota exceeded."""
    def __init__(self, current: int, cap: int, message: str):
        self.current = current
        self.cap = cap
        super().__init__(message)


class RelayError(ToolTrustError):
    """Cloud relay communication error."""
    pass


class VerificationError(ToolTrustError):
    """DDC verification failed."""
    pass