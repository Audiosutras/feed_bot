import discord
import requests
import requests_random_user_agent
from typing import Optional


class Reddit:
    """Reddit

    Reddit API: https://www.reddit.com/dev/api/
    """

    def __init__(self, subreddit: Optional[str], channel_id: Optional[int]):
        self.subreddit = subreddit
        self.channel_id = channel_id

    @property
    def url(self, *args, **kwargs):
        """Url of a subreddit's new posts"""
        return f"https://www.reddit.com/r/{self.subreddit}/new.json?sort=new"

    def get(self, *args, **kwargs):
        response = requests.get(self.url)
        return response.json()

    def get_channel_subreddit_documents(self):
        response = self.get()
        formatted_res = []
        children = response["data"]["children"]
        for child_data in children:
            data = child_data.get("data", {})
            subreddit = data.get("subreddit", "")
            title = data.get("title", "")[:256]
            description = data.get("selftext", "")[:256]
            link = data.get("permalink", "")
            if description:
                formatted_res.append(
                    dict(
                        channel_id=self.channel_id,
                        subreddit=subreddit,
                        title=title,
                        description=description,
                        link=link,
                        sent=False,  # only storing document in db from here
                    )
                )
        return formatted_res

    @staticmethod
    def documents_to_embeds(documents, *args, **kwargs):
        """Static method for converting noSql Documents to Discord Embeds"""
        channel_embeds = []
        for doc in documents:
            embed = discord.Embed(
                title=f"{doc.title}",
                url=f"https://reddit.com{doc.link}",
                description=f"[r/{doc.subreddit}]: {doc.description}",
                color=discord.Colour.from_rgb(255, 0, 0),
            )
            channel_embeds.append((doc.channel_id, embed))
        return channel_embeds
