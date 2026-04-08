class DomainError(Exception):
    pass


class ContextTooLarge(DomainError):
    pass


class IncompleteDraft(DomainError):
    pass


class StaleCompass(DomainError):
    pass


class UnroutableQuery(DomainError):
    pass
