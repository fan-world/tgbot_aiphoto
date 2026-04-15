from __future__ import annotations

from pathlib import Path


class MediaCatalog:
    def __init__(self, assets_dir: Path) -> None:
        self.assets_dir = assets_dir

    def screen(self, key: str, override: str | None = None) -> Path | None:
        if override:
            path = Path(override)
            if path.exists():
                return path

        candidate = self.assets_dir / f"{key}.png"
        return candidate if candidate.exists() else None

