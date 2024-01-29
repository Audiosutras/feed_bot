import discord
import requests
import requests_random_user_agent


class Reddit:
    """Reddit

    Reddit API: https://www.reddit.com/dev/api/
    """

    def __init__(self, subreddit, channel_id):
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

    async def get_embedded_posts(
        self, channel: discord.abc.GuildChannel, *args, **kwargs
    ):
        """Posts only new embeds that we have not previously shared in channel."""
        prior_embed_check = []
        async for message in channel.history(limit=100):
            title = ""
            embeds = getattr(message, "embeds", [])
            if embeds:
                title = getattr(embeds[0], "title")
            prior_embed_check.append(title)

        response = await self.get()
        embeds = []
        children = response["data"]["children"]
        for child_data in children:
            subreddit = child_data["data"]["subreddit"]
            title = child_data["data"]["title"][:256]
            description = child_data["data"]["selftext"][:256]
            link = child_data["data"]["permalink"]
            if description and title not in prior_embed_check:
                embed = discord.Embed(
                    title=f"{title}",
                    url=f"https://reddit.com{link}",
                    description=f"[r/{subreddit}]: {description}",
                    color=discord.Colour.from_rgb(255, 0, 0),
                )
                embeds.append(embed)
        return embeds
