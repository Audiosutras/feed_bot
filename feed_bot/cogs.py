"""Commands for FeedBot registered in FeedBot's setup_hook

https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#cogs
"""
from discord.ext import commands
from .utils.reddit import Reddit


class RedditRSS(commands.Cog):
    """RSS like updates for subreddits from Reddit"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="subreddit")
    async def subreddit(self, ctx: commands.Context) -> None:
        """Group command for managing channel subreddit rss feeds"""
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "**Invalid subreddit command passed. Type: .help subreddit**"
            )

    @subreddit.command(name="add")
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
