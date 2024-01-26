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

    def get_embedded_posts(self, *args, **kwargs):
        response = self.get()
        embeds = []
        children = response["data"]["children"]
        for child_data in children:
            subreddit = child_data["data"]["subreddit"]
            title = child_data["data"]["title"][:256]
            description = child_data["data"]["selftext"][:256]
            link = child_data["data"]["permalink"]
            if description:
                embed = discord.Embed(
                    title=f"{title}",
                    url=f"https://reddit.com{link}",
                    description=f'[r/{subreddit}]: {description}',
                    color=discord.Colour.from_rgb(255, 0, 0),
                )
                embeds.append(embed)
        return embeds
