"""Patch class.
"""

class Patch:
    """
    Represents a patch/update to the game.

    :param build_id: The id of the build.
    :type build_id: int
    :param date: The date that the patch was released.
    :type date: str
    """
    def __init__(self, build_id: int, date: str):
        self.build_id: int = build_id
        self.date: str = date
