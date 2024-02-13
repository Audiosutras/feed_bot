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

    Only guild owner can invoke these commands.

    For help setting up permissions see:
    https://support.discord.com/hc/en-us/articles/206029707-Setting-Up-Permissions-FAQ
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="subreddit")
    @commands.is_owner()
    async def subreddit(self, ctx: commands.Context) -> None:
        """Group command for managing channel subreddit rss feeds"""
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
            {"$group": {"_id": "$channel_id", "subreddits": {"$push": "$subreddit"}}},
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
                    await channel.send(f"**Subreddit Subscriptions: {subreddits_str}**")
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
                await channel.send(f"**Subscribed to r/{subreddit} 'new' listings**")

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
        filter_dict = {"channel_id": channel_id, "subreddit": {"$exists": True}}
        result = await self.bot.reddit_collection.delete_many(filter_dict)
        if result.deleted_count >= 1:
            print(f"Removed all subreddits from channel: {channel_id}")
            await channel.send(f"**Removed subreddit channel subscription**")
        else:
            await channel.send(f"**Already removed subreddit channel subscriptions**")


class RSSFeedCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="rss")
    @commands.is_owner()
    async def rss(self, ctx: commands.Context) -> None:
        async with ctx.typing():
            channel = ctx.message.channel
            embeds = []
            rss = RSSFeed(session=self.bot.http_session, channel_id=channel.id)
            feed_urls = [
                "https://unlimitedhangout.com/feed/",
                "https://corbettreport.com/feed/",
            ]
            ### find

            ### insert
            await rss.get_channel_feeds(feed_urls=feed_urls, feed_key="feed")

            if rss.error:
                return await channel.send(res.error_msg)

            for feed in rss.res_dicts:
                embed = rss.create_about_embed(feed)
                embeds.append(embed)
            await channel.send(embeds=embeds)
