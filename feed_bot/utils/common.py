from aiohttp import ClientSession


class CommonUtilities:
    """CommonUtilities for managing class state and aiohttp sessions"""

    error = False
    error_msg = ""
    res_dicts = []

    def __init__(self, session: ClientSession = None, channel_id: str = ""):
        self.session = session
        self.channel_id = channel_id

    def clear(self):
        self.error = False
        self.error_msg = ""
        self.res_dicts = []
