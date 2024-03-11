from asyncpraw.models.listing.mixins import subreddit
import discord
from typing import List, Tuple
import os
from aiohttp import ClientSession
import asyncpraw
from asyncpraw.exceptions import RedditAPIException, ClientException
from asyncprawcore.exceptions import Redirect, RequestException

from .common import CommonUtilities


class Reddit(CommonUtilities):
    """Utility class for interacting with the reddit api

    Reddit API: https://www.reddit.com/dev/api/
    """

    def __init__(
        self,
        session: ClientSession | None = None,
        subreddit_names: List[str] = [],
        channel_id: int | str = "",
    ) -> None:
        super().__init__(session=session, channel_id=channel_id)
        self.subreddits_query = "+".join(subreddit_names)
        self.reddit = asyncpraw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            password=os.getenv("REDDIT_PASSWORD"),
            requestor_kwargs=dict(session=session),
            user_agent=os.getenv("REDDIT_USER_AGENT"),
            username=os.getenv("REDDIT_USERNAME"),
        )

    async def get_subreddit_submissions(self) -> None:
        self.clear()
        try:
            subreddits = await self.reddit.subreddit(self.subreddits_query)
        except (
            RedditAPIException,
            ClientException,
            RequestException,
        ) as e:
            self.error = True
            self.error_msg = f"{e}"
        else:
            try:
                async for submission in subreddits.new():
                    # Only selfpost (user content) should be shown
                    if getattr(submission, "permalink"):
                        submission_dict = dict(
                            channel_id=self.channel_id,
                            subreddit=submission.subreddit_name_prefixed,
                            title=submission.title,
                            description=submission.selftext,
                            link=submission.permalink,
                            image=submission.thumbnail,
                            sent=False,
                        )
                        self.res_dicts.append(submission_dict)
            except RequestException as e:
                self.error = True
                self.error_msg = (
                    f"**500 Error while retrieving subreddit(s) new listings: {e}**"
                )

    async def check_subreddit_exists(self, subreddit_name: str) -> Tuple[bool, str]:
        """Calls the asyncpraw api and checks whether a given subreddit_name exists"""
        exists: bool = True
        msg: str = f"**r/{subreddit_name} - 200 Ok.**"
        try:
            await self.reddit.subreddit(subreddit_name, fetch=True)
        except RequestException:
            exists = False
            msg = f"**Please add r/{subreddit_name} later.**"
        except Redirect:
            exists = False
            msg = f"**r/{subreddit_name} does not exists.**"
        return (exists, msg)

    def documents_to_embeds(self, documents: List[dict]):
        """A method for converting noSql Documents to Discord Embeds"""
        channel_embeds = []
        for doc in documents:
            title = doc.get("title", "")
            link = doc.get("link", "")
            subreddit = doc.get("subreddit")
            description = doc.get("description", "")
            channel_id = doc.get("channel_id")
            image = doc.get("image", "")
            object_id = doc.get("_id")

            if len(title) > 256:
                title = f"{title[:253]}..."
            if len(description) > 1000:
                description = f"{description[:1000]}..."
            if "https://" not in link:
                link = f"https://www.reddit.com{link}"
            embed = discord.Embed(
                title=title,
                url=link,
                description=f"**[{subreddit}]:** {description}",
                color=discord.Colour.red(),
            )
            if "https://" in image:
                # here this a submission's thumbnail image
                # see get_subreddit_submissions for info
                embed.set_image(url=image)
            if self.IMAGES_URL:
                thumbnail = f"{self.IMAGES_URL}/reddit-logo.png"
                embed.set_thumbnail(url=thumbnail)
            channel_embeds.append((channel_id, embed, object_id))
        return channel_embeds
