"""FeedBot

Ensure that you have BOT_TOKEN loaded as an environment variable
before running this script. Also requires Message Content Intent
to be enabled for Bot

Documentation:
- BOT_TOKEN
    - This is found on the Bot tab under the username for the bot
    - Click `Reset_Token`, and copy the contents of the string shown into
    a .env file
- Message Content Intent
            - Read More: https://discord.com/developers/docs/topics/gateway#message-content-intent
"""
import os
import discord
import asyncio
import aiohttp
from motor import motor_asyncio
from discord.ext import commands, tasks
from .utils.reddit import Reddit
from .cogs import RedditCommands, RSSFeedCommands


LOOP_CYCLE = {"minutes": 60} if os.getenv("PROD_ENV", False) else {"minutes": 1}


class FeedBot(commands.Bot):
    """FeedBot Class Inherited from commands.Bot

    commands.Bot Documentation:
        - https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#bot

    Requires:
        - Message Content Intent
            - Read More: https://discord.com/developers/docs/topics/gateway#message-content-intent
    """

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
        self.http_session = None

    async def setup_hook(self):
        """A coroutine to be called to setup the bot.

        Overwritten method from commands.Bot
        """
        self.http_session = aiohttp.ClientSession()
        print(f"Task Loop Interval: {LOOP_CYCLE}")
        self.subreddit_task.start()
        await self.add_cog(RedditCommands(self))
        await self.add_cog(RSSFeedCommands(self))

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

    async def reddit_find_one_or_insert_one_documents(self, dicts: [dict]):
        """For each dictionary a document is created if a document matching the dictionary is not found.

        This is done to prevent duplicate documents from entering the database as tasks run.

        Args:
            collection: MongoDB collection name
            filter: search dictionary to see if a matching document is within the database
            dicts (dict]): List of dictionaries to become documents
        """

        inserted = []
        for d in dicts:
            doc = await self.reddit_collection.find_one(
                {
                    "channel_id": d.get("channel_id"),
                    "subreddit": d.get("subreddit"),
                    "title": d.get("title"),
                    "description": d.get("description"),
                    "sent": {"$exists": True},
                }
            )
            if not doc:
                result = await self.reddit_collection.insert_one(d)
                inserted.append(result.inserted_id)
        print(f"Of {len(dicts)} new listings {len(inserted)} have been added to db")

    @tasks.loop(**LOOP_CYCLE)
    async def subreddit_task(self, *args, **kwargs):
        await self.pull_subreddit(*args, **kwargs)
        await self.post_subreddit(*args, **kwargs)

    @subreddit_task.before_loop
    async def before_subreddit(self):
        await self.wait_until_ready()  # wait until the bot logs in

    async def pull_subreddit(self, *args, **kwargs):
        """Fetches a channel's subreddit new listings and stores them in the database

        Args:
            ctx (commands.Context): Context object
        """
        pipeline = [
            {
                "$match": {
                    "channel_id": {"$exists": True},
                    "subreddit": {"$exists": True},
                    "title": {"$exists": False},
                    "description": {"$exists": False},
                    "link": {"$exists": False},
                    "sent": {"$exists": False},
                }
            },
            {"$group": {"_id": "$channel_id", "subreddits": {"$push": "$subreddit"}}},
        ]
        cursor = self.reddit_collection.aggregate(pipeline)
        documents = await cursor.to_list(None)
        for doc in documents:
            channel_id = doc.get("_id")
            subreddits = doc.get("subreddits")
            print(f"Channel ID: {channel_id}, Subreddits: {subreddits}")
            r = Reddit(self.http_session, subreddits, channel_id)
            await r.get_subreddit_submissions()
            if r.error:
                channel = self.get_channel(channel_id)
                await channel.send(r.error_msg)
            else:
                await self.reddit_find_one_or_insert_one_documents(r.res_dicts)

    async def post_subreddit(self, *args, **kwargs):
        """Returns new posts for a subreddit"""
        cursor = self.reddit_collection.find({"sent": False})
        unsent_documents = await cursor.to_list(None)
        if unsent_documents:
            r = Reddit()
            channel_embeds = r.documents_to_embeds(documents=unsent_documents)
            for channel_id, embed, doc_id in channel_embeds:
                channel = self.get_channel(channel_id)
                await channel.send(embeds=[embed])
                await self.reddit_collection.update_one(
                    filter={"_id": doc_id}, update={"$set": {"sent": True}}
                )


def main():
    bot = FeedBot()
    token = os.getenv("BOT_TOKEN")
    bot.run(token)
