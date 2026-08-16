# Writing your tool

## Where code goes

Everything lives in `src/my_cool_tool/`. The template ships an `example.py` to
delete or build from.

## Running your code in Maya

While developing, point Maya at your source folder. In Maya's Script Editor:

```python
import sys

sys.path.append("/full/path/to/my-cool-tool/src")

import my_cool_tool.example as example

example.create_locator("test")
```

You only need the `sys.path` line once per Maya session.

Once you [cut a release](releasing.md), users install it properly and none of
this path juggling is needed.

## Adding dependencies

If your tool needs a third-party package:

```sh
uv add some-package
```

That records it in `pyproject.toml` and installs it. When you release, it gets
bundled into the module so users don't have to install anything themselves.
