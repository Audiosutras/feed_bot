"""FeedBot
"""
import os
import discord
import asyncio
from motor import motor_asyncio
from discord.ext import commands, tasks
from dotenv import load_dotenv
from .utils.reddit import Reddit
from .cogs import RedditRSS

load_dotenv()


class FeedBot(commands.Bot):

    database_name = "feed_bot_db"
    reddit_collection = "reddit"

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(
            command_prefix=commands.when_mentioned_or("."), intents=intents
        )
        mongodb_uri = os.getenv("MONGODB_URI")
        self.db_client = motor_asyncio.AsyncIOMotorClient(mongodb_uri)
        self.db = self.db_client[self.database_name]
        self.reddit_collection = self.db[self.reddit_collection]

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


def main():
    bot = FeedBot()
    token = os.getenv("BOT_TOKEN")
    bot.run(token)
