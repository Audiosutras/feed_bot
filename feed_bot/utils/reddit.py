import discord
import os
import pdb
from aiohttp import ClientSession
import asyncpraw
from asyncprawcore.exceptions import ResponseException


class Reddit:
    """Reddit

    Reddit API: https://www.reddit.com/dev/api/
    """

    error = False
    error_msg = ""
    res_dicts = []

    def __init__(
        self,
        session: ClientSession = None,
        subreddit_names: [str] = "",
        channel_id: str = "",
    ) -> None:
        self.subreddits_query = "+".join(subreddit_names)
        self.channel_id = channel_id
        self.reddit = asyncpraw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            password=os.getenv("REDDIT_PASSWORD"),
            requestor_kwargs=dict(session=session),
            user_agent=os.getenv("REDDIT_USER_AGENT"),
            username=os.getenv("REDDIT_USERNAME"),
        )

    def clear(self):
        self.error = False
        self.error_msg = ""
        self.res_dicts = []

    async def get_subreddit_submissions(self, *args, **kwargs) -> None:
        self.clear()
        try:
            subreddits = await self.reddit.subreddit(self.subreddits_query)
        except ResponseException as e:
            self.error = True
            self.error_msg = f"{e}"
        else:
            async for submission in subreddits.new():
                submission_dict = dict(
                    channel_id=self.channel_id,
                    subreddit=submission.subreddit_name_prefixed,
                    title=submission.title,
                    description=submission.selftext[:256],
                    link=submission.url,
                    sent=False,
                )
                self.res_dicts.append(submission_dict)

    @staticmethod
    def documents_to_embeds(documents, *args, **kwargs):
        """Static method for converting noSql Documents to Discord Embeds"""
        channel_embeds = []
        for doc in documents:
            title = doc.get("title")
            link = doc.get("link")
            subreddit = doc.get("subreddit")
            description = doc.get("description")
            channel_id = doc.get("channel_id")
            object_id = doc.get("_id")
            if "https://" not in link:
                link = f"https://www.reddit.com{link}"
            embed = discord.Embed(
                title=f"{title}",
                url=link,
                description=f"[{subreddit}]: {description}",
                color=discord.Colour.from_rgb(255, 0, 0),
            )
            channel_embeds.append((channel_id, embed, object_id))
        return channel_embeds
