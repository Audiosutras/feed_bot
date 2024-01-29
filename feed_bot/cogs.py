"""Commands for FeedBot registered in FeedBot's setup_hook

https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#cogs
"""
from discord.ext import commands
from .utils.reddit import Reddit


class RedditRSS(commands.Cog):
    """RSS like updates for subreddits from Reddit"""

    def __init__(self, bot):
        self.bot = bot

    async def insert_documents(self, documents):
        result = await self.bot.reddit_collection.insert_many(documents)
        print(
            f"inserted {len(result.inserted_ids)} docs into {self.bot.reddit_collection} collection"
        )

    @commands.group(name="subreddit")
    async def subreddit(self, ctx):
        """Group command for managing channel subreddit rss feeds"""
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "**Invalid subreddit command passed. Type: .help subreddit**"
            )

    @subreddit.command(name="add")
    async def add(self, ctx, arg):
        """Adds subreddit as an rss feed for this channel."""
        channel_id = ctx.message.channel.id
        subreddit = arg
        r = Reddit(subreddit, channel_id)
        documents = r.get_channel_subreddit_documents()
        result = await self.insert_documents(documents)
        await ctx.send(f"**Following r/{subreddit}**")

    @subreddit.command(name="start")
    async def start(self, ctx):
        """Stops rss feeds feeds service"""
        self.bot.post_subreddit.start(ctx)
        await ctx.send("**Starting reddit rss feed service...**")

    @subreddit.command(name="stop")
    async def stop(self, ctx):
        """Stops rss feeds feeds service"""
        self.bot.post_subreddit.stop(ctx)
        await ctx.send("**Stopping reddit rss feed service...**")
