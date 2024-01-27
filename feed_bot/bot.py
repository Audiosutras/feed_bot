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
        super().__init__(command_prefix=commands.when_mentioned_or('$'), intents=intents)
    
    async def setup_hook(self):
        await self.add_cog(RedditCog(self))

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

    @tasks.loop(seconds=60)
    async def post_subreddit(self, *args, **kwargs):
        """Returns New Posts for a subreddit"""
        cmd_ctx = kwargs.get("cmd_ctx")
        channel_id = cmd_ctx.message.channel.id
        subreddit = kwargs.get("subreddit")
        channel = self.get_channel(channel_id)
        affiliate_marketing = Reddit(subreddit)
        embeds = await affiliate_marketing.get_embedded_posts(channel)
        if embeds:
            for embed in embeds:
                await channel.send(embed=embed)

    @post_subreddit.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in

class RedditCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="rss_subreddit")
    async def rss_subreddit(self, ctx, arg, *args, **kwargs):
        """Get updates when a new posts has been added to a subreddit
        
        Add subreddit feed: $rss_subreddit <subreddit_name>
        """
        kwargs["cmd_ctx"] = ctx
        kwargs["subreddit"] = arg
        self.bot.post_subreddit.start(*args, **kwargs)
        await ctx.send(f"**Starting For r/{arg}...**")

    @commands.command(name="rm_subreddit")
    async def rm_subreddit(self, ctx):
        """Removes subreddit rss feed"""
        self.bot.post_subreddit.stop()
        await ctx.send("stopping...")
        

def main():
    bot = FeedBot()
    token = os.getenv("BOT_TOKEN")
    bot.run(token)

