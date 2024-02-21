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
        feed_key: Literal["feed", "entries", None] = None,
        *args,
        **kwargs,
    ) -> None:
        """Iterates of feed_urls performing GET requests

        Exceptions:
            - Sets self.error and self.error_msg if an exception is encountered during
            the aiohttp session request. Errors are raised one at a time instead of
            being grouped together. Could be changed at a future date.
            - Also sets self.error and self.error_msg if mal-formed XML is encountered.
            If this error is shown we recommend not adding the url to your channel feeds

        Args:
            feed_urls (str]): A list of feed urls
            feed_key (Literal["feed", "entry", None], optional):
                - Determines the dictionary in the response that will be returned.
                - Defaults to None.
                - If None a tuple of dictionaries are returned (feed, entry)

        Returns:
            None. Note that self.error, self.error_msg, and self.res_dicts are inherited attributes
            from CommonUtilities and comprise the state of our object.
        """
        self.clear()
        for url in feed_urls:
            if url:
                try:
                    feed_data = await self.get_rss_feed(url=url)
                except HTTPException as e:
                    self.error = True
                    self.error_msg = (
                        f"An error occurred while fetching an rss feed: {e} "
                        f"Channel ID: {self.channel_id}, URL: {url}"
                    )
                    break
                else:
                    if feed_data.get("bozo", 1) == 1:
                        self.error = True
                        self.error_msg = (
                            f"Not well-formed XML "
                            f"Channel ID: {self.channel_id}, URL: {url}"
                        )
                        break
                    if feed_key is None:
                        feed = feed_data.get("feed")
                        entries = feed_data.get("entries")
                        data = (feed, entries)
                    else:
                        data = feed_data.get(feed_key)
                    self.res_dicts.append(data)

    @staticmethod
    def parse_feed_flat(feed: dict) -> [str | dict]:
        """Receives a feed dictionary and converts it to a list

        Args:
            feed (dict): Value of the "feed" key in feed_data

        Returns:
            [str | dict]: Returns a List of strings and/or dictionaries
        """
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

    @staticmethod
    def parse_entry_flat(entry: dict) -> [str | dict]:
        """Receives an entry dictionary and converts it to a list

        Args:
            entry (dict): Value of an entry. From the "entries" key in feed_data

        Returns:
            [str | dict]: Returns a List of strings and/or dictionaries
        """
        feed_url: str = entry.get("feed_url", "")
        title: str = entry.get("title", "")
        thumbnail: str = entry.get("thumbnail", "")
        summary: str = entry.get("summary", "")
        author_detail: dict = entry.get("author_detail", {})
        link: str = entry.get("link", "")
        published: str = entry.get("published", "")
        content: str = entry.get("content", "")
        description = summary or content

        return [
            feed_url,
            title,
            thumbnail,
            summary,
            author_detail,
            link,
            published,
            content,
            description,
        ]

    def create_about_embed(self, feed: dict) -> discord.Embed:
        """Converts a feed dictionary into a discord Embed.

        Args:
            feed (dict): Value of the "feed" key in feed_data

        Returns:
            discord.Embed: Represents a Discord embed.
        """
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

        if image:
            embed.set_thumbnail(url=image)
        if author_name := author_detail.get("name"):
            embed.set_author(name=author_name[:256])
        if email := author_detail.get("email"):
            embed.add_field(name="contact", value=email[:256], inline=False)
        embed.add_field(name="feed url", value=feed_url, inline=False)
        return embed

    def create_entry_embed(self, entry: dict) -> discord.Embed:
        """Converts an entry dictionary into a discord Embed.

        Args:
            entry (dict): Value of an entry. From the "entries" key in feed_data

        Returns:
            discord.Embed: Represents a Discord embed.
        """
        (
            feed_url,
            title,
            thumbnail,
            summary,
            author_detail,
            link,
            published,
            content,
            description,
        ) = self.parse_entry_flat(entry)

        embed = discord.Embed(
            title=title,
            url=link,
            description=description[:4096],
            color=discord.Colour.teal(),
        )
        if published:
            embed.add_field(name="published", value=published, inline=False)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if author_name := author_detail.get("name"):
            embed.set_author(name=author_name[:256])
        if email := author_detail.get("email"):
            embed.add_field(name="contact", value=email[:256], inline=False)
        embed.add_field(name="feed url", value=feed_url, inline=False)
        return embed
