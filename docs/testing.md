# Testing

## Writing a test

Tests go in `tests/maya/`, where you'll find this example ready to uncomment:

```python
def test_create_locator_expects_locator_created():
    # Arrange
    from my_cool_tool.example import create_locator
    from maya import cmds

    # Act
    test_loc = create_locator("foo")

    # Assert
    assert cmds.objExists(test_loc)
```

Two rules:

- The file is named `test_*.py` and the function `test_*`. That's how they get
  found.
- Import `maya` *inside* the function, not at the top of the file. Outside Maya
  that import fails and breaks the whole test run.

## Running tests locally

Tests run under `mayapy`:

```sh
# --python must match your Maya version (2024 = 3.10, 2025/2026 = 3.11)
uv venv --managed-python --python 3.11 .venv-maya
uv pip install --python .venv-maya --group test .
PYTHONPATH=.venv-maya/lib/python3.11/site-packages mayapy -m pytest tests
```

This needs an alias to `mayapy`, or swap it for the full path.

Any Maya tests you set up will also run automatically
[on GitHub](ci.md) when you push.
