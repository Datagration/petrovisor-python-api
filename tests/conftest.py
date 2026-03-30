import os
from pathlib import Path

import petrovisor as pv
import pytest

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass


@pytest.fixture
def api():
    return pv.PetroVisor(
        workspace=os.environ.get("TEST_WORKSPACE"),
        discovery_url=os.environ.get("TEST_URL"),
        key=os.environ.get("TEST_KEY"),
    )
