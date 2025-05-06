import os
from pathlib import Path
import uuid
import requests
from pytubefix import Channel
from app.utils.database import Database
from app.models import YouTubeChannelSource
from minio.deleteobjects import DeleteObject
from app.utils.minioStorage import MinioStorage, BUCKET

database = Database().get_session()
minio_client = MinioStorage().get_client()
temp_directory = "./temp/"

class YoutubeChannel():
    def add_channel(self, channel_url) -> YouTubeChannelSource:
        channel = Channel(channel_url)
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