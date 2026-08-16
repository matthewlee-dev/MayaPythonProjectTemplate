# Releasing

A release turns your code into something a user can install.

## Building a release

On GitHub, go to **Actions** → **Release** → **Run workflow**, then type the
version number (e.g. `1.2.4`).

GitHub bumps the version, runs the checks, tags the code, builds the zip, and
publishes it on your repo's Releases page. Your
[docs site](documentation.md) updates separately, on push.

The other three fields only apply if your tool has dependencies:

- **Vendor runtime dependencies** bundles your dependencies into the module, so
  the user doesn't have to install them. Untick to leave them out.
- **Maya versions** and **Platforms** decide which combinations those
  dependencies are built for.

## From the command line

`release.py` works out the next version for you and starts the same workflow:

```sh
python3 release.py --bump patch
```

| | from `1.2.3` |
|---|---|
| `--bump patch` | `1.2.4` |
| `--bump minor` | `1.3.0` |
| `--bump major` | `2.0.0` |

Run it from `main` with everything committed and pushed. Add `--dry-run` to
check the version and preflight without triggering the release.

## What users get

A zip on your Releases page. They extract it and drag
`my_cool_tool_drag_and_drop_installer.py` into a Maya viewport, which copies the
tool into Maya's modules folder. Any dependencies are bundled in.

## Testing the package first

Build it locally without releasing:

```sh
python3 scripts/build_module.py --clean
```

That stages everything in `dist/`, so you can drag
`dist/my_cool_tool_drag_and_drop_installer.py` into Maya to try the real
install.
