"""Commands for FeedBot

Commands initialized in setup_hook for FeedBot in bot.py

Cogs Documentation:
https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#cogs
"""
import discord
from discord.ext import commands
from .utils.reddit import Reddit
from .utils.rss import RSSFeed


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
        await channel.send(f"**Getting subreddits...**")
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
                    channel_id = doc.get("_id")
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
                    await self.bot.reddit_collection.insert_one(doc_dict)
                    await channel.send(
                        f"**Subscribed to r/{subreddit} 'new' listings**"
                    )

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
                await channel.send(f"**Removed subreddit channel subscription**")
            else:
                await channel.send(
                    f"**Already removed subreddit channel subscriptions**"
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
        if "," in arg:
            feed_urls = arg.split(",")
        else:
            feed_urls = [arg]
        await channel.send(f"**Getting feeds...**")
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
                    f"**Channel Already Subscribed to RSS Feeds:**",
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
                    f"**New RSS Feed Subscriptions:**", embeds=db_insert_embeds
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
