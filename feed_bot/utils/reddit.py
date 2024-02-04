import discord
import requests
from requests.exceptions import HTTPError, ConnectionError
import requests_random_user_agent
from typing import Optional


class Reddit:
    """Reddit

    Reddit API: https://www.reddit.com/dev/api/
    """

    error = False
    res_dicts = []

    def __init__(self, subreddit="", channel_id=""):
        self.subreddit = subreddit
        self.channel_id = channel_id

    @property
    def url(self, *args, **kwargs):
        """Url of a subreddit's new posts"""
        return f"https://www.reddit.com/r/{self.subreddit}/new.json?sort=new"

    def get(self, *args, **kwargs):
        self.error = False
        self.error_msg = ""
        try:
            response = requests.get(self.url)
        except (HTTPError, ConnectionError) as e:
            self.error = True
            self.error_msg = f"**Error occurred while connecting with reddit api: {e}**"
            print(error_msg)  # log error message
            return error_msg
        else:
            if response.ok:
                return response.json()
            self.error = True
            self.error_msg = (
                f"**Received {response.status_code} for subreddit: {self.subreddit}**"
            )
            return self.error_msg

    def get_channel_subreddit_dicts(self):
        response = self.get()
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
