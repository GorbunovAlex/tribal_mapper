from dataclasses import dataclass

from domain.exceptions import ContextTooLargeError

DEFAULT_TOKEN_CEILING = 1000


@dataclass(frozen=True)
class TokenCount:
    value: int
    ceiling: int = DEFAULT_TOKEN_CEILING

    def __post_init__(self) -> None:
        if self.value > self.ceiling:
            raise ContextTooLargeError(
                f"Token count {self.value} exceeds ceiling {self.ceiling}"
            )
