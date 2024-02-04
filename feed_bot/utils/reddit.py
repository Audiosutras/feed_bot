import discord
from aiohttp import ClientError
from typing import Optional


class Reddit:
    """Reddit

    Reddit API: https://www.reddit.com/dev/api/
    """

    error = False
    res_dicts = []

    def __init__(self, session=None, subreddit="", channel_id=""):
        self.session = session
        self.subreddit = subreddit
        self.channel_id = channel_id

    @property
    def url(self, *args, **kwargs):
        """Url of a subreddit's new posts"""
        return f"https://www.reddit.com/r/{self.subreddit}/new.json?sort=new"

    async def request(self, method, *args, **kwargs):
        """Handles Get Requests for self.url"""
        self.error = False
        self.error_msg = ""
        try:
            match method:
                case "get":
                    resp = await self.session.get(self.url, raise_for_status=True)
                    async with resp:
                        return resp.json()
                case _:
                    self.error = True
                    self.error_msg = f"**Method {method} not set.**"
                    return self.error_msg
        except ClientError as e:
            self.error = True
            self.error_msg = f"**Error occurred while connecting with reddit api: {e}**"
            print(error_msg)  # log error message
            return error_msg

    async def get_channel_subreddit_dicts(self):
        response = await self.request(method="get")
        if not self.error:
            children = response["data"]["children"]
            for child_data in children:
                data = child_data.get("data", {})
                subreddit = data.get("subreddit", "")
                title = data.get("title", "")[:256]
                description = data.get("selftext", "")[:256]
                link = data.get("permalink", "")
                if description:
                    return self.res_dicts.append(
                        dict(
                            channel_id=self.channel_id,
                            subreddit=subreddit,
                            title=title,
                            description=description,
                            link=link,
                            sent=False,  # only storing document in db from here
                        )
                    )

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
            embed = discord.Embed(
                title=f"{title}",
                url=f"https://reddit.com{link}",
                description=f"[r/{subreddit}]: {description}",
                color=discord.Colour.from_rgb(255, 0, 0),
            )
            channel_embeds.append((channel_id, embed, object_id))
        return channel_embeds
