import os
from aiohttp import ClientSession


IMAGE_MIME_TYPES = [
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/svg+xml",
    "image/gif",
    "image/apng",
    "image/avif",
]


class CommonUtilities:
    """CommonUtilities for managing class state and aiohttp sessions"""

    IMAGES_URL = os.getenv("IMAGES_URL", "")
    error = False
    error_msg = ""
    res_dicts = []

    def __init__(self, session: ClientSession = None, channel_id: int | None = None):
        self.session = session
        self.channel_id = channel_id

    def clear(self):
        self.error = False
        self.error_msg = ""
        self.res_dicts = []
