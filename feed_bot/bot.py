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

    async def setup_hook(self):
        await self.add_cog(RedditRSS(self))

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

    @tasks.loop(seconds=60)
    async def pull_subreddit(self, ctx, *args, **kwargs):
        """Fetches subreddit new listings and stores them in the database

        Args:
            ctx (commands.Context): Context object
        """
        cursor = self.reddit_collection.find(
            {
                "channel_id": {"$exists": True},
                "subreddit": {"$exists": True},
                "title": {"$exists": False},
                "description": {"$exists": False},
                "link": {"$exists": False},
                "sent": {"$exists": False},
            }
        )
        documents = await cursor.to_list(None)
        for doc in documents:
            channel_id = doc.get("channel_id")
            subreddit = doc.get("subreddit")
            print(f"Channel ID: {channel_id}, Subreddit: {subreddit}")
            r = Reddit(subreddit, channel_id)
            r.get_channel_subreddit_dicts()
            if r.error:
                channel = self.get_channel(channel_id)
                await channel.send(r.error_msg)
            else:
                await self.reddit_find_one_or_insert_one_documents(r.res_dicts)

    @tasks.loop(seconds=60)
    async def post_subreddit(self, ctx, *args, **kwargs):
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

    @post_subreddit.before_loop
    async def before_post_subreddit(self):
        await self.wait_until_ready()  # wait until the bot logs in

    @pull_subreddit.before_loop
    async def before_pull_subreddit(self):
        await self.wait_until_ready()


def main():
    bot = FeedBot()
    token = os.getenv("BOT_TOKEN")
    bot.run(token)
