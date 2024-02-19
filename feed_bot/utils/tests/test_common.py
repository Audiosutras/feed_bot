import pytest
from aiohttp import web

from ..common import CommonUtilities


class TestCommonUtilites:
    @pytest.mark.asyncio
    async def test__init__(self, aiohttp_client):
        c = CommonUtilities()
        assert c.session is None
        assert c.channel_id == ""
        channel_id = "32432423423"
        app = web.Application()
        session = await aiohttp_client(app)
        c1 = CommonUtilities(session=session, channel_id=channel_id)
        assert c1.session == session
        assert c1.channel_id == channel_id
