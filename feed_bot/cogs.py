"""Commands for FeedBot

Commands initialized in setup_hook for FeedBot in bot.py

Cogs Documentation:
https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#cogs
"""

import re
import tempfile
from typing import List, Dict
import discord
from discord.ext import commands

from feed_bot.utils.common import REDDIT_URL_PATTERN
from feed_bot.utils.reddit import Reddit
from feed_bot.utils.rss import RSSFeed


class FileCommands(commands.Cog):
    """Commands for exporting channel subscriptions

    Channel members can export a channel's subscriptions
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="export")
    async def export_channel_subs(self, ctx: commands.Context) -> None:
        """Sends a generated .txt file of all the channel's subscriptions to the channel"""
        async with ctx.typing():
            channel = ctx.message.channel
            pipeline = [
                {
                    "$lookup": {
                        "from": self.bot.reddit_collection_str,
                        "localField": "channel_id",
                        "foreignField": "channel_id",
                        "pipeline": [
                            {
                                "$match": {
                                    "channel_id": {"$exists": True},
                                    "subreddit": {"$exists": True},
                                    "title": {"$exists": False},
                                    "description": {"$exists": False},
                                    "link": {"$exists": False},
                                    "sent": {"$exists": False},
                                }
                            },
                        ],
                        "as": "reddit_docs",
                    }
                },
                {"$unwind": "$reddit_docs"},
                {
                    "$project": {
                        "_id": 1,
                        "channel_id": 1,
                        "feed_url": 1,
                        "subreddit": "$reddit_docs.subreddit",
                    }
                },
                {"$match": {"channel_id": channel.id}},
                {
                    "$group": {
                        "_id": "$channel_id",
                        "feed_urls": {"$addToSet": "$feed_url"},
                        "subreddits": {"$addToSet": "$subreddit"},
                    }
                },
            ]

            cursor = self.bot.rss_collection.aggregate(pipeline)
            documents: List = await cursor.to_list(None)
            if documents:
                doc: Dict = documents[0]
                feed_urls: List[str] = doc.get("feed_urls", [])
                subreddits: List[str] = doc.get("subreddits", [])

                if feed_urls or subreddits:
                    to_file_write: Dict = {
                        ".rss add": ",".join(feed_urls),
                        ".subreddit add": ",".join(subreddits),
                    }

                    with tempfile.NamedTemporaryFile(
                        mode="w+t", suffix=".txt", delete_on_close=False
                    ) as fp:
                        for key, value in to_file_write.items():
                            fp.write(f"{key} {value}\n")
                        fp.close()

                        filename = f"{channel.name}.txt"
                        file = discord.File(fp.name, filename=filename)
                        await channel.send(
                            content=f"**Channel Subscriptions Export: {filename}**",
                            file=file,
                        )
                else:
                    await channel.send(
                        content="**Channel has no subscriptions to export**"
                    )
            else:
                await channel.send(content="**Channel has no subscriptions to export**")


class RedditCommands(commands.Cog):
    """RSS like updates for subreddits from Reddit

    Only the guild owner can invoke these commands.

    For help setting up permissions see:
    https://support.discord.com/hc/en-us/articles/206029707-Setting-Up-Permissions-FAQ
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="subreddit")
    @commands.is_owner()
    async def subreddit(self, ctx: commands.Context) -> None:
        """Commands for managing channel subreddits"""
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "**Invalid subreddit command passed. Type: .help subreddit**"
            )

    @subreddit.command(name="ls")
    @commands.is_owner()
    async def ls(self, ctx: commands.Context) -> None:
        """List the subreddits that this channel subscribes to.

        Args:
            ctx (commands.Context): context object
        """
        channel = ctx.message.channel
        await channel.send("**Getting subreddits...**")
        async with ctx.typing():
            pipeline = [
                {
                    "$match": {
                        "channel_id": channel.id,
                        "subreddit": {"$exists": True},
                        "title": {"$exists": False},
                        "description": {"$exists": False},
                        "link": {"$exists": False},
                        "sent": {"$exists": False},
                    }
                },
                {
                    "$group": {
                        "_id": "$channel_id",
                        "subreddits": {"$push": "$subreddit"},
                    }
                },
            ]
            cursor = self.bot.reddit_collection.aggregate(pipeline)
            documents = await cursor.to_list(None)
            if not documents:
                await channel.send("**No Subreddit Subscriptions**")
            else:
                for doc in documents:  # should be only 1 document
                    subreddits = doc.get("subreddits")
                    subreddits_str = ", ".join(subreddits)
                    if subreddits:  # this always should be the case
                        await channel.send(
                            f"**Subreddit Subscriptions: {subreddits_str}**"
                        )
                    else:
                        await channel.send("**No Subreddit Subscriptions**")

    @subreddit.command(name="add")
    @commands.is_owner()
    async def add(self, ctx: commands.Context, arg: str) -> None:
        """Add subreddit(s) as an rss feed for this channel.

        If a user is trying to add a subreddit that is already in the db for a channel the
        existing document is returned. If a subreddit for a channel is not already in the
        db the subreddit is created in the db.

        Args:
            ctx (commands.Context): Invocation Context Object
            arg (str):
                - the subreddit or comma separated list of subreddits to add.
                - https://www.reddit.com/r/<subreddit>/, r/<subreddit> or <subreddit> is acceptable
        """
        async with ctx.typing():
            channel = ctx.message.channel
            channel_id = channel.id
            subreddit_arg = arg
            # Parse comma seperated list if given
            if "," in arg:
                subreddit_arg = arg.split(",")
            else:
                subreddit_arg = [arg]

            for subreddit in subreddit_arg:
                # Validation
                if subreddit.startswith(("https://", "http://")):
                    if re.fullmatch(REDDIT_URL_PATTERN, subreddit):
                        subreddit = subreddit.split("m/")[
                            1
                        ]  # split at the end of '.com/'
                        if subreddit.endswith("/"):
                            subreddit = subreddit[:-1]
                    else:
                        await channel.send(
                            f"**Not a valid reddit url for subreddit: {subreddit}**"
                        )
                        break
                if subreddit.startswith("r/"):
                    subreddit = subreddit[2:]

                # Find or Insert logic
                doc_dict = {"channel_id": channel_id, "subreddit": subreddit}
                filter_dict = {
                    **doc_dict,
                    "title": {"$exists": False},
                    "description": {"$exists": False},
                    "link": {"$exists": False},
                    "sent": {"$exists": False},
                }
                doc = await self.bot.reddit_collection.find_one(filter_dict)
                if doc:
                    await channel.send(f"**Already subscribed to r/{subreddit}**")
                else:
                    r = Reddit(session=self.bot.http_session, channel_id=channel_id)
                    exists, msg = await r.check_subreddit_exists(
                        subreddit_name=subreddit
                    )
                    if exists:
                        await self.bot.reddit_collection.insert_one(doc_dict)
                        await channel.send(
                            f"**Subscribed to r/{subreddit} 'new' listings**"
                        )
                    else:
                        await channel.send(content=msg)

    @subreddit.command(name="rm")
    @commands.is_owner()
    async def rm(self, ctx: commands.Context, arg: str) -> None:
        """Remove rss feed of subreddit(s) from this channel

        Removes both the "reference" marking document and unsent documents
        with the same channel_id and subreddit
        Args:
            ctx (commands.Context): Invocation Context Object
            arg (str):
                - the subreddit or comma separated list of subreddits to remove.
                - r/<subreddit> or <subreddit> is acceptable
        """
        channel = ctx.message.channel
        channel_id = channel.id
        subreddit_arg = arg
        if "," in arg:
            subreddit_arg = arg.split(",")
        else:
            subreddit_arg = [arg]

        async with ctx.typing():
            for sa in subreddit_arg:
                subreddit = sa
                if sa.startswith("r/"):
                    subreddit = sa[2:]
                filter_dict = {"channel_id": channel_id, "subreddit": subreddit}
                result = await self.bot.reddit_collection.delete_many(filter_dict)
                if result.deleted_count >= 1:
                    print(f"Removed r/{subreddit} from channel: {channel_id}")
                    await channel.send(
                        f"**Removed subscription to r/{subreddit} 'new' listings**"
                    )
                else:
                    await channel.send(
                        f"**Already not subscribed to r/{subreddit} 'new' listings**"
                    )

    @subreddit.command(name="prune")
    @commands.is_owner()
    async def prune(self, ctx: commands.Context) -> None:
        """Removes all subreddit rss feeds within a given channel

        Args:
            ctx (commands.Context): Invocation Context Object
        """
        channel = ctx.message.channel
        channel_id = channel.id
        async with ctx.typing():
            filter_dict = {"channel_id": channel_id, "subreddit": {"$exists": True}}
            result = await self.bot.reddit_collection.delete_many(filter_dict)
            if result.deleted_count >= 1:
                print(f"Removed all subreddits from channel: {channel_id}")
                await channel.send("**Removed subreddit channel subscription**")
            else:
                await channel.send(
                    "**Already removed subreddit channel subscriptions**"
                )


class RSSFeedCommands(commands.Cog):
    """RSS feed updates within your guild channels

    Only the guild owner can invoke these commands.

    For help setting up permissions see:
    https://support.discord.com/hc/en-us/articles/206029707-Setting-Up-Permissions-FAQ
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="rss")
    @commands.is_owner()
    async def rss(self, ctx: commands.Context) -> None:
        """Commands for managing channel rss feeds"""
        if ctx.invoked_subcommand is None:
            await ctx.send("**Invalid subreddit command passed. Type: .help rss**")

    @rss.command(name="ls")
    @commands.is_owner()
    async def ls(self, ctx: commands.Context) -> None:
        """List the RSS Feeds that this channel subscribes to.

        Args:
            ctx (commands.Context): Invocation Context Object

        Returns:
            None
        """
        async with ctx.typing():
            channel = ctx.message.channel
            pipeline = [
                {
                    "$match": {
                        "channel_id": channel.id,
                        "feed_url": {"$exists": True},
                    }
                },
                {
                    "$group": {
                        "_id": "$channel_id",
                        "feeds": {
                            "$push": {
                                "feed_url": "$feed_url",
                                "title": "$title",
                                "subtitle": "$subtitle",
                                "summary": "$summary",
                                "description": "$description",
                                "author_detail": "$author_detail",
                                "link": "$link",
                                "image": "$image",
                            }
                        },
                    }
                },
            ]
            cursor = self.bot.rss_collection.aggregate(pipeline)
            documents = await cursor.to_list(None)
            embeds = []
            rss = RSSFeed()
            if not documents:
                await channel.send("**No RSS Feed Subscriptions**")
            else:
                for doc in documents:
                    for feed in doc.get("feeds"):
                        feed = {**feed, "image": {"href": feed.get("image")}}
                        embed = rss.create_about_embed(feed=feed)
                        embeds.append(embed)
                await channel.send("**Channel RSS Subscriptions:**", embeds=embeds)

    @rss.command(name="add")
    @commands.is_owner()
    async def add(self, ctx: commands.Context, arg: str) -> None:
        """Adds website rss feeds to the channel.

        Args:
            ctx (commands.Context): Invocation Context Object
            arg (str):
                - the url or comma separated list of urls for the rss feeds to be added
                - url with or without trailing slash is acceptable

        Returns:
            None: Nothing is returned from this definition
        """
        channel = ctx.message.channel
        feed_urls: list = []
        # Parse comma seperated list if given
        if "," in arg:
            feed_urls = arg.split(",")
        else:
            feed_urls = [arg]
        await channel.send("**Getting feeds...**")
        async with ctx.typing():
            db_found_embeds = []
            to_insert = []
            rss = RSSFeed(session=self.bot.http_session, channel_id=channel.id)

            for url in feed_urls:
                url = url if url.endswith("/") else f"{url}/"

                filter_dict = dict(channel_id=channel.id, feed_url=url)
                doc = await self.bot.rss_collection.find_one(filter_dict)

                if doc:

                    feed = {**doc, "image": {"href": doc["image"]}}
                    embed = rss.create_about_embed(feed=feed)
                    db_found_embeds.append(embed)
                else:
                    to_insert.append(url)

            if db_found_embeds:
                await channel.send(
                    "**Channel Already Subscribed to RSS Feeds:**",
                    embeds=db_found_embeds,
                )

            if to_insert:
                await rss.parse_feed_urls(feed_urls=to_insert)

                if rss.error:
                    return await channel.send(f"**{rss.error_msg}**")

                db_insert_embeds = []
                for feed, entries in rss.res_dicts:
                    (
                        feed_url,
                        title,
                        subtitle,
                        summary,
                        description,
                        author_detail,
                        link,
                        image,
                    ) = rss.parse_feed_flat(feed)

                    await self.bot.rss_collection.insert_one(
                        {
                            "channel_id": channel.id,
                            "feed_url": feed_url,
                            "title": title,
                            "subtitle": subtitle,
                            "summary": summary,
                            "description": description,
                            "author_detail": author_detail,
                            "link": link,
                            "image": image,
                        }
                    )

                    await self.bot.find_one_rss_entry_or_insert(
                        feed_url=feed_url, thumbnail=image, entries=entries
                    )

                    embed = rss.create_about_embed(feed=feed)
                    db_insert_embeds.append(embed)

                await channel.send(
                    "**New RSS Feed Subscriptions:**", embeds=db_insert_embeds
                )

    @rss.command(name="rm")
    @commands.is_owner()
    async def rm(self, ctx: commands.Context, arg: str) -> None:
        """Removes specific rss feeds from channel
        Args:
            ctx (commands.Context): Invocation Context Object
            arg (str):
                - the url or comma separated list of urls for the rss feeds to be added
                - url with or without trailing slash is acceptable
        """
        async with ctx.typing():
            channel = ctx.message.channel
            feed_urls: list = []
            if "," in arg:
                feed_urls = arg.split(",")
            else:
                feed_urls = [arg]

            embeds = []
            for url in feed_urls:
                url = url if url.endswith("/") else f"{url}/"
                filter_dict = {"channel_id": channel.id, "feed_url": url}
                doc = await self.bot.rss_collection.find_one_and_delete(filter_dict)
                if doc:
                    feed = {**doc, "image": {"href": doc["image"]}}
                    title = feed.get("title")
                    print(f"Removed {title} from channel: {channel.id}")
                    rss = RSSFeed()
                    embed = rss.create_about_embed(feed=feed)
                    embeds.append(embed)

            if embeds:
                return await channel.send(
                    f"**Removed RSS Feed Subscription:**", embeds=embeds
                )
            return await channel.send(f"**Already Unsubscribed**")

    @rss.command(name="prune")
    @commands.is_owner()
    async def prune(self, ctx: commands.Context) -> None:
        """Removes all web rss feeds within a given channel

        Args:
            ctx (commands.Context): Invocation Context Object
        """
        async with ctx.typing():
            channel = ctx.message.channel
            channel_id = channel.id
            filter_dict = {"channel_id": channel_id, "feed_url": {"$exists": True}}
            result = await self.bot.rss_collection.delete_many(filter_dict)
            if result.deleted_count >= 1:
                print(f"Removed all web rss feeds from channel: {channel_id}")
                await channel.send(f"**Removed web rss feed channel subscription**")
            else:
                await channel.send(f"**Already web rss feed channel subscriptions**")
