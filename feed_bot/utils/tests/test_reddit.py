from unittest.mock import AsyncMock, MagicMock
import pytest
import asyncpraw
from asyncpraw.exceptions import RedditAPIException, RedditErrorItem
from aiohttp import web

from ..reddit import Reddit


class TestReddit:
    """Test Reddit Class (utility class)"""

    channel_id = "32432423423"
    subreddit_names = ["linux", "cyberDeck"]

    @pytest.mark.asyncio
    async def test__init__(self, aiohttp_client, mocker):
        asyncpraw_reddit = mocker.patch.object(asyncpraw, "Reddit")
        app = web.Application()
        expected_session = await aiohttp_client(app)
        r = Reddit(
            session=expected_session,
            channel_id=self.channel_id,
            subreddit_names=self.subreddit_names,
        )

        expected_subreddits_query = "+".join(self.subreddit_names)
        assert r.subreddits_query == expected_subreddits_query
        assert r.session == expected_session
        asyncpraw_reddit.assert_called_once()
