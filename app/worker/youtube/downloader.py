import os
import uuid
import ffmpeg
import logging
import requests
from pathlib import Path
from pytubefix import YouTube
from app.utils.logger import get_logger
from app.utils.database import Database
from minio.deleteobjects import DeleteObject
from app.models import Video, YouTubeChannelSource
from app.worker.youtube.channel import YoutubeChannel
from app.utils.minioStorage import MinioStorage, BUCKET
from app.worker.proxy.proxy_manager import ProxyManager

database = Database().get_session()
minio_client = MinioStorage().get_client()
proxy_manager = ProxyManager()
logger = get_logger('worker_logger', logging.DEBUG)


class YoutubeDownloader():
    def __init__(self, enable_proxy=False):
        self.__temp_directory__ = "./temp/"
        self.enable_proxy = enable_proxy

    def download(self, video_url: str):
        audio_filename = uuid.uuid4()
        video_filename = uuid.uuid4()
        thumbnail_filename = uuid.uuid4()
        video_db_id = -1
        try:
            youtube_video = self.get_video_instance(video_url, self.enable_proxy)

            if self.is_video_present_in_db(youtube_video):
                logger.info(f"Video ({youtube_video.title}) already exists")
                return

            logger.debug(f"Start download of video: {youtube_video.video_id} - {youtube_video.title}")

            self.download_thumbnail(youtube_video.video_id, youtube_video.thumbnail_url)
            logger.debug(f"Thumbnail downloaded of {youtube_video.video_id} - {youtube_video.title}")

            video_itag = self.get_video_itag(youtube_video)
            audio_itag = self.get_audio_itag(youtube_video)

            youtube_video.streams.get_by_itag(video_itag).download(self.__temp_directory__, filename_prefix=f"{youtube_video.video_id}_video_")
            youtube_video.streams.get_by_itag(audio_itag).download(self.__temp_directory__, filename_prefix=f"{youtube_video.video_id}_audio_")

            audio_file = [f for f in os.listdir(self.__temp_directory__) if f.startswith(f"{youtube_video.video_id}_audio_")][0]
            self.convert_m4a_to_mp3(f"{self.__temp_directory__}{audio_file}", f"{self.__temp_directory__}{youtube_video.video_id}_final_audio.mp3")

            logger.debug(f"MP3 created of {youtube_video.video_id} - {youtube_video.title}")

            self.combine_audio_video(youtube_video.video_id)

            logger.debug(f"Final Video created of {youtube_video.video_id} - {youtube_video.title}")
            
            self.upload_video_and_audio(youtube_video.video_id, audio_filename, video_filename, thumbnail_filename)
            video_db_id = self.write_in_database(youtube_video, f"{video_filename}.mp4", f"{audio_filename}.mp3", f"{thumbnail_filename}.jpg")

            logger.info(f"Video {youtube_video.video_id} - {youtube_video.title} successfully downloaded")
        
        except Exception as e:
            logger.error(f"Error during download of video ({youtube_video.title})", exc_info=True)
            self.clean_up_on_error(str(video_filename))
            self.clean_up_on_error(str(audio_filename))
            self.clean_up_on_error(str(thumbnail_filename))
        finally:
            self.clean_up(youtube_video.video_id)

        return video_db_id

    def get_video_instance(self, video_url: str, enable_proxy: bool) -> YouTube:
        if enable_proxy:
            return YouTube(video_url, proxies=proxy_manager.get_next_proxy())
        return YouTube(video_url)
        
    def is_video_present_in_db(self, video: YouTube) -> bool:
        db_video = database.query(Video).where(Video.external_id==video.video_id).first()
        if db_video:
            return True
        return False

    def get_video_itag(self, video: YouTube):
        preferred_resolutions = ["1080p", "720p", "480p", "360p"]
        streams = video.streams.filter(file_extension="mp4", only_video=True)

        for res in preferred_resolutions:
            stream = streams.filter(res=res).first()
            if stream:
                return stream.itag

        logger.warning(f"No matching video stream found. ({video.title})")
        return None

    def get_audio_itag(self, video: YouTube):
        preferred_resolutions = ["160kbps", "128kbps", "48kbps"]
        streams = video.streams.filter(only_audio=True)

        for abr in preferred_resolutions:
            stream = streams.filter(abr=abr).first()
            if stream:
                return stream.itag

        logger.warning(f"No matching audio stream found. ({video.title})")
        return None

    def convert_m4a_to_mp3(self, input_file: str, output_file: str):
        ffmpeg.input(input_file).output(output_file, **{
            'codec:a': 'libmp3lame',
            'qscale:a': 2
        }).run()

    def combine_audio_video(self, video_id: str):
        video_files = [f for f in os.listdir(self.__temp_directory__) if f.startswith(f"{video_id}_video_")]
        audio_files = [f for f in os.listdir(self.__temp_directory__) if f.startswith(f"{video_id}_audio_")]

        if not video_files or not audio_files:
            raise FileNotFoundError("Video or audio file not found.")

        video_path = os.path.join(self.__temp_directory__, video_files[0])
        audio_path = os.path.join(self.__temp_directory__, audio_files[0])
        output_path = os.path.join(self.__temp_directory__, f"{video_id}_final_video.mp4")

        video_input = ffmpeg.input(video_path)
        audio_input = ffmpeg.input(audio_path)

        ffmpeg.output(video_input, audio_input, output_path, vcodec='copy', acodec='aac', strict='experimental', shortest=None).run()

    def upload_video_and_audio(self, video_id: str, audio_filename: str, video_filename: str, thumbnail_filename: str):
        final_video_path = Path(f"{self.__temp_directory__}{video_id}_final_video.mp4")
        audio_path = Path(f"{self.__temp_directory__}{video_id}_final_audio.mp3")
        thumbnail_path = Path(f"{self.__temp_directory__}{video_id}_thumbnail.jpg")

        self.upload_to_object_storage(final_video_path, video_filename)
        self.upload_to_object_storage(audio_path, audio_filename)
        self.upload_to_object_storage(thumbnail_path, thumbnail_filename)

    def download_thumbnail(self, video_id: str, thumbnail_url: str):
        response = requests.get(thumbnail_url)

        if response.status_code == 200:
            with open(f'{self.__temp_directory__}{video_id}_thumbnail.jpg', 'wb') as file:
                file.write(response.content)
        else:
            logger.error(f"Failed to download thumbnail (Video Id: {video_id})")

    def write_in_database(self, video: YouTube, video_file_name: str, audio_file_name: str, thumbnail_file_name: str):
        channel = database.query(YouTubeChannelSource).where(YouTubeChannelSource.channel_id==video.channel_id).first()
        if not channel:
            channel = YoutubeChannel().add_channel(video.channel_url)

        video_data = Video(
            source_id=channel.id,
            external_id=video.video_id,
            title=video.title,
            author=video.author,
            description=video.description,
            length=video.length,
            thumbnail_url=video.thumbnail_url,
            published_at=video.publish_date,
            video_path=video_file_name,
            audio_path=audio_file_name,
            thumbnail_path=thumbnail_file_name
        )

        database.add(video_data)
        database.commit()

        return video_data.id

    def upload_to_object_storage(self, file, filename: str):
        file_extension = file.name.split(".")[-1]
        with file.open("rb") as file_data:
            minio_client.put_object(
                BUCKET, f"{filename}.{file_extension}", file_data,
                length=-1,
                part_size=10*1024*1024,
            )

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
            logger.error(f"Error during Minio CleanUp (Prefix: {filename_prefix})")


    def clean_up(self, video_id: str):
        for filename in os.listdir(self.__temp_directory__):
            if filename.startswith(video_id):
                file_path = os.path.join(self.__temp_directory__, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)


