import os
from pathlib import Path
import uuid
import requests
from pytubefix import YouTube, Channel
from app.utils.database import Database
from app.models import Video, YouTubeChannelSource
from minio.deleteobjects import DeleteObject
from app.utils.minioStorage import MinioStorage, BUCKET
from app.worker.proxy.proxy_manager import ProxyManager

database = Database().get_session()
minio_client = MinioStorage().get_client()
temp_directory = "./temp/"
proxy_manager = ProxyManager()

class YoutubeChannel():
    def __init__(self, enable_proxy=False):
        self.enable_proxy = enable_proxy
        
    def get_new_video_urls(self) -> list[str]:
        new_videos = []
        channels_to_monitor = database.query(YouTubeChannelSource).where(YouTubeChannelSource.auto_download).all()

        for channel_to_monitor in channels_to_monitor:
            print(channel_to_monitor.name)
            channel = self.get_channel_instance(channel_to_monitor.url, self.enable_proxy)

            for video in channel.videos:
                if not self.is_video_present(video.video_id):
                    new_videos.append(video.watch_url)
        
        return new_videos

    def add_channel(self, channel_url) -> YouTubeChannelSource:
        channel = self.get_channel_instance(channel_url, self.enable_proxy)
        filename = uuid.uuid4()

        channel_source = YouTubeChannelSource(
            channel_id=channel.channel_id,
            name=channel.channel_name,
            url=channel.channel_url,
            thumbnail_url=channel.thumbnail_url,
            thumbnail_path=str(filename) + ".jpg"
        )

        if self.is_channel_present_in_db(channel):
            print("already present")
            return database.query(YouTubeChannelSource).where(YouTubeChannelSource.channel_id==channel.channel_id).first()
        
        try:
            temp_path = Path(self.download_thumbnail(channel.channel_id, channel.thumbnail_url))
            self.upload_to_object_storage(temp_path, filename)

            database.add(channel_source)
            database.commit()
        except Exception as e:
            print("Fuck: ", e)
            self.clean_up_on_error(str(filename))
        finally:
            self.clean_up(channel.channel_id)

        return channel_source
    
    def get_channel_instance(self, channel_url: str, enable_proxy) -> Channel:
        if enable_proxy:
            return Channel(channel_url, proxies=proxy_manager.get_next_proxy())
        return Channel(channel_url)

    
    def is_channel_present_in_db(self, channel: Channel) -> bool:
        db_channel = database.query(YouTubeChannelSource).where(YouTubeChannelSource.channel_id==channel.channel_id).first()
        if db_channel:
            return True
        return False
    
    def download_thumbnail(self, channel_id: str, thumbnail_url: str):
        response = requests.get(thumbnail_url)
        filename = f'{temp_directory}{channel_id}_thumbnail.jpg'

        if response.status_code == 200:
            with open(filename, 'wb') as file:
                file.write(response.content)
        else:
            print("Failed")
        
        return filename
    
    def upload_to_object_storage(self, file: str, filename: str):
        file_extension = file.name.split(".")[-1]
        with file.open("rb") as file_data:
            minio_client.put_object(
                BUCKET, f"{filename}.{file_extension}", file_data,
                length=-1,
                part_size=10*1024*1024,
            )
        
    def clean_up(self, channel_id: str):
        for filename in os.listdir(temp_directory):
            if filename.startswith(channel_id):
                file_path = os.path.join(temp_directory, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
    
    def clean_up_on_error(self, filename_prefix):
        try:
            objects_to_delete = minio_client.list_objects(
                BUCKET,
                prefix=filename_prefix,
                recursive=True
            )
            delete_object_list = [
                DeleteObject(obj.object_name) for obj in objects_to_delete if obj and obj.object_name
            ]
    
            if delete_object_list:
                list(minio_client.remove_objects(BUCKET, delete_object_list))

        except Exception as e:
            print("S3Error:", e)

    def is_video_present(self, video_id: str):
        video = database.query(Video).where(Video.external_id == video_id).first()
        if video: 
            return True
        return False