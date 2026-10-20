from pathlib import Path

import pytest


@pytest.fixture
def datos_dir() -> Path:
    return Path(__file__).parent / "datos"
