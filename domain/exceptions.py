class DomainError(Exception):
    pass


class ContextTooLargeError(DomainError):
    pass


class IncompleteDraftError(DomainError):
    pass


class StaleCompassError(DomainError):
    pass


class UnroutableQueryError(DomainError):
    pass
