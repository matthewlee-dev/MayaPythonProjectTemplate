import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def add_root_to_sys_path():
    root_dir = Path(__file__).resolve().parent.parent / "src"
    sys.path.insert(0, str(root_dir))
