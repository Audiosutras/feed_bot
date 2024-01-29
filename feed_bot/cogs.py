"""Commands for FeedBot registered in FeedBot's setup_hook

https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#cogs
"""
import asyncio
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
        await ctx.send(f"**{result}**")

    @subreddit.command(name="start")
    async def start(self, ctx, arg, *args, **kwargs):
        """Adds and starts subreddit rss feeds for this channel."""
        kwargs["cmd_ctx"] = ctx
        kwargs["subreddit"] = arg
        self.bot.post_subreddit.start(*args, **kwargs)
        await ctx.send(f"**Starting For r/{arg}...**")

    @start.error
    async def handle_start_cmd_error(self, ctx, error):
        await ctx.send(f"**{error}**")
        await ctx.send(f"**CMD: .subreddit start <subreddit_name>**")

    @subreddit.command(name="stop")
    async def stop(self, ctx):
        """Stops and removes subreddit rss feeds from this channel."""
        self.bot.post_subreddit.stop()
        await ctx.send("stopping...")
