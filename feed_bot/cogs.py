"""Commands for FeedBot registered in FeedBot's setup_hook

https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#cogs
"""
from discord.ext import commands
from .utils.reddit import Reddit


class RedditRSS(commands.Cog):
    """RSS like updates for subreddits from Reddit"""

    collection = "reddit"

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="subreddit")
    async def subreddit(self, ctx):
        """Group command for managing channel subreddit rss feeds"""
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "**Invalid subreddit command passed. Type: .help subreddit**"
            )

    @subreddit.command(name="add")
    async def add(self, ctx, arg):
        """Add subreddit(s) as an rss feed for this channel.

        If a user is trying to add a subreddit that is already in the db for a channel the
        existing document is returned. If a subreddit for a channel is not already in the
        db the subreddit is created in the db.
        """
        channel = ctx.message.channel
        channel_id = channel.id
        subreddit = arg
        if arg.includes(","):
            subreddit = arg.split(",")
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

    @subreddit.command(name="start")
    async def start(self, ctx):
        """Stops rss feeds feeds service"""
        self.bot.post_subreddit.start(ctx)
        self.bot.pull_subreddit.start(ctx)
        await ctx.send("**Starting reddit rss feed service...**")

    @subreddit.command(name="stop")
    async def stop(self, ctx):
        """Stops rss feeds feeds service"""
        self.bot.post_subreddit.stop()
        self.bot.pull_subreddit.stop()
        await ctx.send("**Stopping reddit rss feed service...**")
