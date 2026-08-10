import pytest

@pytest.fixture(scope="session", autouse=True)
def run_in_maya():
    from maya import (
        standalone,
        cmds
    )
    standalone.initialize()
    cmds.scriptEditorInfo(e=True, sw=True, se=True, si=True)
    yield
    standalone.uninitialize()