import discord
import requests
import requests_random_user_agent


class Reddit:
    def __init__(self, subreddit):
        self.subreddit = subreddit

    @property
    def url(self, *args, **kwargs):
        """Url of a subreddit's new posts

        Returns:
            _type_: _description_
        """
        return f"https://www.reddit.com/r/{self.subreddit}/new.json?sort=new"

    def get(self, *args, **kwargs):
        response = requests.get(self.url)
        return response.json()

    def get_embedded_posts(self, *args, **kwargs):
        response = self.get()
        children = response["data"]["children"]
        for child_data in children:
            subreddit = child_data["data"]["subreddit"]
            title = child_data["data"]["title"]
            description = child_data["data"]["selftext"][:256]
            link = child_data["data"]["permalink"]
            embeds = []
            if description:
                embed = discord.Embed(
                    title=f"{title} [r/{subreddit}]",
                    url=f"https://reddit.com{link}",
                    description=description,
                    color=discord.Colour.from_rgb(255, 0, 0),
                )
                embeds.append(embed)
            return embeds
