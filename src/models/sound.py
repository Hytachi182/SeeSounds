from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Sound:
    id: int
    name: str
    filepath: Path
    start_offset: float = 0.0
    enabled: bool = True
    category: Optional[str] = None
