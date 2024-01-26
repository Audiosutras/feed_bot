# This example requires the 'message_content' intent.
import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from .utils.reddit import Reddit

load_dotenv()


class FeedClient(discord.Client):
    async def setup_hook(self) -> None:
        # start the task to run in the background
        self.post_affiliate_marketing_reddit.start()

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

    @tasks.loop(hours=24)
    async def post_affiliate_marketing_reddit(self):
        """Returns New Posts In Affiliate Reddit"""
        channel = self.get_channel(1198396321409802372)
        affiliate_marketing = Reddit("Affiliatemarketing")
        embeds = affiliate_marketing.get_embedded_posts()
        for embed in embeds:
            await channel.send(embed=embed)

    @post_affiliate_marketing_reddit.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in


def main():
    # Discord permissions
    intents = discord.Intents.default()
    intents.message_content = True

    # initialize Bot
    bot = RedditClient(command_prefix="$", intents=intents)

    token = os.getenv("BOT_TOKEN")
    bot.run(token)


if __name__ == "__main__":
    main()
