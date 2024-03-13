import os
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter

REDDIT_URL_PATTERN = "https://(www\.)reddit\.com/r/[a-zA-Z0-9./]+(/)?"

IMAGE_MIME_TYPES = [
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/svg+xml",
    "image/gif",
    "image/apng",
    "image/avif",
]


def md(soup: BeautifulSoup, **options):
    """Convert BeautifulSoup instance to markdown text"""
    return MarkdownConverter(**options).convert_soup(soup)


class CommonUtilities:
    """CommonUtilities for managing class state and aiohttp sessions"""

    IMAGES_URL = os.getenv("IMAGES_URL", "")
    error = False
    error_msg = ""
    res_dicts = []

    def __init__(
        self, session: ClientSession | None = None, channel_id: int | str = ""
    ):
        self.session = session
        self.channel_id = channel_id

    def clear(self):
        self.error = False
        self.error_msg = ""
        self.res_dicts = []
