import pytest
from aiohttp import web

from ..common import CommonUtilities


class TestCommonUtilities:
    """Test CommonUtilities class"""

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

    def test_clear(self):
        error = True
        error_msg = "test_error_msg"
        res_dicts = [{"a_key": "b_value"}, {"c_key": "d_value"}]
        c = CommonUtilities()
        c.error = error
        c.error_msg = error_msg
        c.res_dicts = res_dicts

        assert c.error == error
        assert c.error_msg == error_msg
        assert c.res_dicts == res_dicts

        # clear
        c.clear()

        assert c.error == False
        assert c.error_msg == ""
        assert c.res_dicts == []
