"""
Patch class.
"""

class Patch:
    """
    A class to represent a patch to the game.

    :param build_id: The id of the build.
    :type build_id: int
    :param date: The date that the patch was released.
    :type date: str
    """
    def __init__(self, build_id, date):
        self.build_id = build_id
        self.date = date

    build_id : int = None
    date : str = None
