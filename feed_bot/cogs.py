"""Commands for FeedBot registered in FeedBot's setup_hook

https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#cogs
"""
from discord.ext import commands
from .utils.reddit import Reddit


class RedditRSS(commands.Cog):
    """RSS like updates for subreddits from Reddit"""

    def __init__(self, bot):
        self.bot = bot

    async def find_one_or_insert_one_documents(self, dicts: [dict]):
        """For each dictionary a document is created if a document matching the dictionary is not found.

        This is done to prevent duplicate documents from entering the database as tasks run.

        Args:
            dicts (dict]): List of dictionaries
        """
        inserted = []
        for d in dicts:
            doc = await self.bot.reddit_collection.find_one(
                {
                    "channel_id": d.get("channel_id"),
                    "subreddit": d.get("subreddit"),
                    "title": d.get("title"),
                    "description": d.get("description"),
                }
            )
            if not doc:
                result = await self.bot.reddit_collection.insert_one(d)
                inserted.append(result.inserted_id)
        print(f"Of {len(dicts)} new listings {len(inserted)} have been added to db")

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
        result = await self.find_one_or_insert_one_documents(dicts)
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
