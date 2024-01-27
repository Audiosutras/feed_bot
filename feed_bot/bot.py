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
    async def post_subreddit(self):
        """Returns New Posts In Affiliate Reddit"""
        channel = self.get_channel(1198396321409802372)
        affiliate_marketing = Reddit("Affiliatemarketing")
        embeds = await affiliate_marketing.get_embedded_posts(channel)
        if embeds:
            for embed in embeds:
                await channel.send(embed=embed)

    # @post_subreddit.before_loop
    # async def before_my_task(self):
    #     await self.wait_until_ready()  # wait until the bot logs in

class RedditCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="rss_subreddit")
    async def rss_subreddit(self, ctx):
        """Get updates when a new posts has been added to a subreddit
        
        Command: $rss_subreddit <subreddit_name>
        """
        self.bot.post_subreddit.start()
        await ctx.send("starting...")

    @commands.command(name="rm_subreddit")
    async def rm_subreddit(self, ctx):
        """Removes subreddit rss feed"""
        self.bot.post_subreddit.stop()
        await ctx.send("stopping...")
        

def main():
    bot = FeedBot()
    token = os.getenv("BOT_TOKEN")
    bot.run(token)

