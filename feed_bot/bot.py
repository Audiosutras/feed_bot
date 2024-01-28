# This example requires the 'message_content' intent.
import os
import discord
import asyncio
from discord.ext import commands, tasks
from dotenv import load_dotenv
from .utils.reddit import Reddit

load_dotenv()


class FeedBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(
            command_prefix=commands.when_mentioned_or("."), intents=intents
        )

    async def setup_hook(self):
        await self.add_cog(RedditRSS(self))

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

    @tasks.loop(seconds=60)
    async def post_subreddit(self, *args, **kwargs):
        """Returns new posts for a subreddit"""
        cmd_ctx = kwargs.get("cmd_ctx")
        channel = cmd_ctx.message.channel
        subreddit = kwargs.get("subreddit")
        affiliate_marketing = Reddit(subreddit)
        embeds = await affiliate_marketing.get_embedded_posts(channel)
        if embeds:
            for embed in embeds:
                await channel.send(embed=embed)

    @post_subreddit.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in


class RedditRSS(commands.Cog):
    """Interact with Reddit Listings"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="subreddit")
    async def subreddit(self, ctx):
        """Group command for managing channel subreddit rss feeds"""
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "**Invalid subreddit command passed. Type: .help subreddit**"
            )

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


def main():
    bot = FeedBot()
    token = os.getenv("BOT_TOKEN")
    bot.run(token)
