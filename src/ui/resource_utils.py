from pathlib import Path
from typing import Optional

from core.config_manager import get_program_dir


def get_asset_path(filename: str) -> Optional[str]:
    asset_path = Path(get_program_dir()) / "assets" / filename
    if not asset_path.exists():
        return None
    return str(asset_path)
