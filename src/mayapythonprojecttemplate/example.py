"""mayapythonprojecttemplate package."""

from maya import cmds


def create_locator(name: str = "") -> str:
    """Create a locator with the given name.

    Args:
        name (str): The name to give the locator.

    Returns:
        str: The name of the locator that was created.
    """
    return cmds.spaceLocator(name=name)[0]
