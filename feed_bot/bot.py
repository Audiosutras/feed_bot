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
import time
import asyncio
import discord
import aiohttp
from datetime import datetime
from motor import motor_asyncio
from discord.ext import commands, tasks
from .utils.reddit import Reddit
from .utils.rss import RSSFeed
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
    reddit_collection_str = "reddit"
    rss_collection_str = "rss"

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(
            command_prefix=commands.when_mentioned_or("."), intents=intents
        )
        mongodb_uri = os.getenv("MONGODB_URI")
        self.db_client = motor_asyncio.AsyncIOMotorClient(mongodb_uri)
        self.db = self.db_client[self.database_name]
        self.reddit_collection = self.db[self.reddit_collection_str]
        self.rss_collection = self.db[self.rss_collection_str]
        self.http_session = None

    async def setup_hook(self):
        """A coroutine to be called to setup the bot.

        Overwritten method from commands.Bot
        """
        self.http_session = aiohttp.ClientSession()
        print(f"Task Loop Interval: {LOOP_CYCLE}")
        self.subreddit_task.start()
        self.rss_feeds_task.start()
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
        """Fetches a channel's subreddit new listings and stores them in the database"""
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

    @tasks.loop(**LOOP_CYCLE)
    async def rss_feeds_task(self, *args, **kwargs):
        await self.update_all_rss_feeds(*args, **kwargs)

    @rss_feeds_task.before_loop
    async def before_rss_feeds_task(self):
        await self.wait_until_ready()

    async def update_all_rss_feeds(self) -> None:
        """Sends RSS Feed Updates to subscribed channels.

        Gathers distinct feed_urls from the rss collection and checks if new entries have been added.
        If entries have been added, channel_ids that subscribe to an updated rss feed receive the new
        entries as an embed.

        This definition is the core logic of the rss_feeds_task.

        Returns:
            None
        """
        rss = RSSFeed(session=self.http_session)
        feed_urls: list = await self.rss_collection.distinct(key="feed_url")
        await rss.parse_feed_urls(feed_urls=feed_urls)
        if rss.error:
            return print(f"An error occurred updating rss feeds: {rss.error_msg}")
        prep_embeds = []
        for feed, entries in rss.res_dicts:
            parsed_feed = rss.parse_feed_flat(feed)
            feed_url = parsed_feed[0]
            thumbnail = parsed_feed[-1]
            inserted_entries = await self.find_one_rss_entry_or_insert(
                feed_url=feed_url, thumbnail=thumbnail, entries=entries
            )
            if inserted_entries:
                pipeline = [
                    {"$match": {"feed_url": feed_url, "channel_id": {"$exists": True}}},
                    {
                        "$group": {
                            "_id": "$feed_url",
                            "channel_ids": {"$addToSet": "$channel_id"},
                        }
                    },
                ]
                cursor = self.rss_collection.aggregate(pipeline)
                documents = await cursor.to_list(None)
                ## create embeds for inserted entries and send to channels we just aggregated
                embeds = []
                for entry in inserted_entries:
                    embed = rss.create_entry_embed(entry=entry)
                    embeds.append(embed)

                for doc in documents:
                    channel_ids: list = doc.get("channel_ids")
                    for channel_id in channel_ids:
                        channel = self.get_channel(channel_id)
                        await channel.send(f"**Feed Updates**", embeds=embeds)

    async def find_one_rss_entry_or_insert(
        self,
        feed_url: str = "",
        thumbnail: str = "",
        entries: [dict] = {},
        *args,
        **kwargs,
    ) -> [dict]:
        """For each entry a document is created in the rss collection if a matching document for the entry is not found.

        Unlike reddit_find_one_or_insert_one_document at this time, entries are stored with out a channel_id.
        The feed_url acts as the unique key. See update_all_rss_feeds for how this works for returning new feed_url entries
        to channels with that given feed_url.

        Args:
            feed_url (str, optional): _description_. Defaults to "".
            thumbnail (str, optional): _description_. Defaults to "".
            entries (dict], optional): _description_. Defaults to {}.

        Returns:
            [dict]: List of entries that are to be added to the rss collection
        """
        inserted = []
        for entry in entries:
            seconds_since_epoch = time.mktime(entry.published_parsed)
            dt = datetime.fromtimestamp(seconds_since_epoch)
            insert_dict = {
                "feed_url": feed_url,
                "thumbnail": thumbnail,
                "dt_published": dt,
                **entry,
            }
            doc = await self.rss_collection.find_one(insert_dict)

            if not doc:
                result = await self.rss_collection.insert_one(insert_dict)
                if result.inserted_id:
                    inserted.append(insert_dict)
        print(
            f"Of {len(entries)} entries for {feed_url} {len(inserted)} have been added to db"
        )
        return inserted


def main():
    bot = FeedBot()
    token = os.getenv("BOT_TOKEN")
    bot.run(token)
