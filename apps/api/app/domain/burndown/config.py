from dataclasses import dataclass


@dataclass(frozen=True)
class BurndownConfig:
    flatline_threshold_days: int = 2

    def __post_init__(self) -> None:
        if type(self.flatline_threshold_days) is not int or self.flatline_threshold_days < 1:
            raise ValueError("flatline_threshold_days must be a positive integer")
