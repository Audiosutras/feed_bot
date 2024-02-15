import discord
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

    async def parse_feed_urls(
        self,
        feed_urls: [str],
        feed_key: Literal["feed", "entries"] = "entries",
        *args,
        **kwargs,
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
                if feed_data.get("bozo", 1) == 1:
                    self.error = True
                    self.error_msg = (
                        f"Not well-formed XML "
                        f"Channel ID: {self.channel_id}, URL: ${url}"
                    )
                    break
                data = feed_data.get(feed_key)
                self.res_dicts.append(data)

    @staticmethod
    def parse_feed_flat(feed: dict) -> [str | dict]:
        title: str = feed.get("title", "")
        subtitle: str = feed.get("subtitle", "")
        summary: str = feed.get("summary", "")
        author_detail: dict = feed.get("author_detail", {})
        link: str = feed.get("link", "")
        image: str = feed.get("image", {}).get("href", "")

        description: str = summary or subtitle

        feed_url = feed.get("feed_url", "")
        for l in feed.get("links", []):
            if l.get("type") == "application/rss+xml":
                feed_url = l.get("href")
                break

        return [
            feed_url,
            title,
            subtitle,
            summary,
            description,
            author_detail,
            link,
            image,
        ]

    def create_about_embed(self, feed: dict) -> discord.Embed:
        (
            feed_url,
            title,
            subtitle,
            summary,
            description,
            author_detail,
            link,
            image,
        ) = self.parse_feed_flat(feed)

        embed = discord.Embed(
            title=title,
            url=link,
            description=description[:4096],
            color=discord.Colour.teal(),
        )
        print(feed)
        print("feed_url", feed_url)
        if image:
            embed.set_thumbnail(url=image)
        if author_name := author_detail.get("name"):
            embed.set_author(name=author_name[:256])
        if email := author_detail.get("email"):
            embed.add_field(name="contact", value=email[:256], inline=False)
        embed.add_field(name="feed url", value=feed_url, inline=False)
        return embed
