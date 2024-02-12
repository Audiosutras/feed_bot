import feedparser
from aiohttp.web import HTTPException
from .common import CommonUtilities
from typing import Literal


class RSSFeed(CommonUtilities):
    """Utility class for interacting with website rss feeds"""

    async def get_rss_feed(self, url: str):
        """Fetch an rss feed within the aiohttp session and have feedparser parse the response text"""
        async with self.session.get(url) as response:
            rss = await response.text()
            return feedparser.parse(rss)

    async def get_channel_feeds(
        self, feed_urls: [str], feed_key: Literal["feed", "entries"], *args, **kwargs
    ) -> None:
        self.clear()
        for url in feed_urls:
            try:
                feed_data = await self.get_rss_feed(url=url)
            except HTTPException as e:
                self.error = True
                self.error_msg = (
                    f"An error occurred while fetching an rss feed: {e} "
                    f"Channel ID: {self.channel_id}, URL: ${url}"
                )
                break
            else:
                print(feed_data.get("bozo"))
                if feed_data.get("bozo", 1) == 1:
                    self.error = True
                    self.error_msg = (
                        f"Not well-formed XML "
                        f"Channel ID: {self.channel_id}, URL: ${url}"
                    )
                    break
                data = feed_data.get(feed_key)
                self.res_dicts.append(data)
