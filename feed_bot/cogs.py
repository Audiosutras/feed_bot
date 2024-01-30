"""Commands for FeedBot registered in FeedBot's setup_hook

https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#cogs
"""
from discord.ext import commands
from .utils.reddit import Reddit


class RedditRSS(commands.Cog):
    """RSS like updates for subreddits from Reddit"""

    def __init__(self, bot):
        self.bot = bot

    async def insert_documents(self, dicts):
        results = []
        for d in dicts:
            result = await self.bot.reddit_collection.update_one(
                filter={
                    "channel_id": d.get("channel_id"),
                    "subreddit": d.get("subreddit"),
                    "title": d.get("title"),
                    "description": d.get("description"),
                    # This field should always exist. So only upsert new dictionaries
                    "sent": {"$exists": False},
                },
                update={"$set": {**d}},
                upsert=True,
            )
            results.append(result)
        print(results)

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
        dicts = r.get_channel_subreddit_dicts()
        result = await self.insert_documents(dicts)
        await ctx.send(f"**Following r/{subreddit}**")

    @subreddit.command(name="start")
    async def start(self, ctx):
        """Stops rss feeds feeds service"""
        self.bot.post_subreddit.start(ctx)
        await ctx.send("**Starting reddit rss feed service...**")

    @subreddit.command(name="stop")
    async def stop(self, ctx):
        """Stops rss feeds feeds service"""
        self.bot.post_subreddit.stop()
        await ctx.send("**Stopping reddit rss feed service...**")
