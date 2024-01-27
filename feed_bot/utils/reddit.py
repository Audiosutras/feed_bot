import discord
import requests
import requests_random_user_agent


class Reddit:
    """Reddit 
    
    Reddit API: https://www.reddit.com/dev/api/
    """
    def __init__(self, subreddit):
        self.subreddit = subreddit

    @property
    def url(self, *args, **kwargs):
        """Url of a subreddit's new posts
        """
        return f"https://www.reddit.com/r/{self.subreddit}/new.json?sort=new"

    def get(self, *args, **kwargs):
        response = requests.get(self.url)
        return response.json()

    async def get_embedded_posts(self, channel: discord.abc.GuildChannel , *args, **kwargs):
        """Posts only new embeds that we have not previously shared in channel.

        Args:
            channel (_type_): discord.abc.GuildChannel

        Returns:
            _type_: _description_
        """
        prior_embed_check = [
            message.embeds[0].title
            async for message in channel.history(limit=100)
        ]
        response = self.get()
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
                    description=f'[r/{subreddit}]: {description}',
                    color=discord.Colour.from_rgb(255, 0, 0),
                )
                embeds.append(embed)
        return embeds
