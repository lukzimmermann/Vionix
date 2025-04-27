from pytubefix import Channel

from app.models import YouTubeChannelSource
from app.utils.database import Database

database = Database()

class YoutubeChannel():
    def add_channel(self, channel_url) -> YouTubeChannelSource:
        session = database.get_session()
        channel = Channel(channel_url)

        channel_source = YouTubeChannelSource(
            channel_id=channel.channel_id,
            name=channel.channel_name,
            url=channel.channel_url,
            thumbnail_url=channel.thumbnail_url
        )

        session.add(channel_source)
        session.commit()

        return channel_source