from unittest.mock import AsyncMock, MagicMock
import pytest
import asyncpraw
from asyncpraw.exceptions import RedditAPIException
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

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "new_listings_list, expected_len_res_dicts, error",
        [
            (
                [
                    {
                        "subreddit_name_prefixed": "r/linux",
                        "title": "Linux Mint Related Post Should Pass With Permalink - User Provided Content",
                        "selftext": "This is the post shown as the description in an embed.",
                        "permalink": "https://www.reddit.com/r/linux/this-is-a-test/",
                    },
                    {
                        "subreddit_name_prefixed": "r/cyberDeck",
                        "title": "Linux Mint Related Post Should Pass With Permalink - User Provided Content",
                        "selftext": "This is the post shown as the description in an embed.",
                        "permalink": "https://www.reddit.com/r/cyberDeck/this-is-a-test",
                    },
                ],
                2,
                None,
            ),
            (
                [
                    {
                        "subreddit_name_prefixed": "r/linux",
                        "title": "Linux Mint Related Post Should Pass With Permalink - User Provided Content",
                        "selftext": "This is the post shown as the description in an embed.",
                        "permalink": "https://www.reddit.com/r/linux/this-is-a-test/",
                    },
                    {
                        "subreddit_name_prefixed": "r/cyberDeck",
                        "title": "Shouldn't Be Added Without Permalink - Ad/Reddit Generated Content",
                        "selftext": "This is the post shown as the description in an embed.",
                        "permalink": "",  # not user generated (selfpost)
                    },
                ],
                1,
                None,
            ),
            (
                [
                    {
                        "subreddit_name_prefixed": "r/linux",
                        "title": "Linux Mint Related Post Should Pass With Permalink - User Provided Content",
                        "selftext": "This is the post shown as the description in an embed.",
                        "permalink": "https://www.reddit.com/r/linux/this-is-a-test/",
                    },
                    {
                        "subreddit_name_prefixed": "r/cyberDeck",
                        "title": "Shouldn't Be Added Without Permalink - Ad/Reddit Generated Content",
                        "selftext": "This is the post shown as the description in an embed.",
                        "permalink": "",  # not user generated (selfpost)
                    },
                ],
                0,
                RedditAPIException,
            ),
        ],
    )
    async def test_get_subreddit_submissions(
        self, mocker, new_listings_list, expected_len_res_dicts, error
    ):
        mock_reddit = mocker.patch.object(asyncpraw, "Reddit", return_value=AsyncMock())
        mock_subreddit = mocker.patch.object(asyncpraw.Reddit, "subreddit")
        if error:
            mock_subreddit.side_effect = error
            mock_reddit.subreddit = mock_subreddit
        else:
            mock_subreddit_model = mocker.patch("asyncpraw.models.Subreddit")
            mock_subreddit.new.return_value = new_listings_list

        r = Reddit(channel_id=self.channel_id, subreddit_names=self.subreddit_names)

        await r.get_subreddit_submissions()
        if error:
            assert r.error == True
            assert r.error_msg == f"{RedditAPIException}"
            assert len(r.res_dicts) == expected_len_res_dicts
        else:
            expected_subreddits_query = "+".join(self.subreddit_names)
            assert len(r.res_dicts) == expected_len_res_dicts
            for submission in r.res_dicts:
                assert submission.sent == False
