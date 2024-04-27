import os
import petrovisor as pv
import pytest


@pytest.fixture
def api():
    return pv.PetroVisor(workspace=os.environ.get("TEST_WORKSPACE"),
                         discovery_url=os.environ.get("TEST_URL"),
                         key=os.environ.get("TEST_KEY"))
