import os
import time 
import uuid
import ffmpeg
from amqp import Channel
from pathlib import Path
from pytubefix import YouTube
from app.utils.database import Database
from app.models import Video, YouTubeChannelSource
from app.worker.youtube.channel import YoutubeChannel
from app.utils.minioStorage import MinioStorage, BUCKET

database = Database().get_session()
minio_client = MinioStorage().get_client()

proxy = {
    "http": "socks5://170.80.203.46:999",
}

class YoutubeDownloader():
    def __init__(self):
        self.__temp_directory__ = "./temp/"
        pass

    def download(self, video_url: str):
        youtube_video = YouTube(video_url, proxies=proxy)

        if self.is_video_present_in_db(youtube_video):
            print("already present")
            return "already present"
        
        print(f"Download {youtube_video.title}")
        
        video_itag = self.get_video_itag(youtube_video)
        audio_itag = self.get_audio_itag(youtube_video)

        youtube_video.streams.get_by_itag(video_itag).download(self.__temp_directory__, filename_prefix=f"{youtube_video.video_id}_video_")
        youtube_video.streams.get_by_itag(audio_itag).download(self.__temp_directory__, filename_prefix=f"{youtube_video.video_id}_audio_")

        audio_file = [f for f in os.listdir(self.__temp_directory__) if f.startswith(f"{youtube_video.video_id}_audio_")][0]
        self.convert_m4a_to_mp3(f"{self.__temp_directory__}{audio_file}", f"{self.__temp_directory__}{youtube_video.video_id}_final_audio.mp3")

        self.combine_audio_video(youtube_video.video_id)

        filename = uuid.uuid4()
        self.upload_video_and_audio(youtube_video.video_id, filename)
        self.write_in_database(youtube_video, f"{filename}.mp4", f"{filename}.mp3")
        self.clean_up(youtube_video.video_id)

        print("finished")

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

        print("No matching stream found.")
        return None

    def get_audio_itag(self, video: YouTube):
        preferred_resolutions = ["160kbps", "128kbps", "48kbps"]
        streams = video.streams.filter(only_audio=True)

        for abr in preferred_resolutions:
            stream = streams.filter(abr=abr).first()
            if stream:
                return stream.itag

        print("No matching stream found.")
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


    def upload_video_and_audio(self, video_id: str, filename: str):
        final_video_path = Path(f"{self.__temp_directory__}{video_id}_final_video.mp4")
        audio_path = Path(f"{self.__temp_directory__}{video_id}_final_audio.mp3")

        self.upload_to_object_storage(final_video_path, filename)
        self.upload_to_object_storage(audio_path, filename)

    def write_in_database(self, video: YouTube, video_file_name: str, audio_file_name: str):
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
            audio_path=audio_file_name
        )

        database.add(video_data)
        database.commit()

    def upload_to_object_storage(self, file, filename: str):
        file_extension = file.name.split(".")[-1]
        with file.open("rb") as file_data:
            minio_client.put_object(
                BUCKET, f"{filename}.{file_extension}", file_data,
                length=-1,
                part_size=10*1024*1024,
            )

    def clean_up(self, video_id: str):
        for filename in os.listdir(self.__temp_directory__):
            if filename.startswith(video_id):
                file_path = os.path.join(self.__temp_directory__, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)

youtube = YoutubeDownloader()
youtube.download("https://www.youtube.com/watch?v=IyEp7qLy_XM")

# from pytubefix import Channel

# url = "https://www.youtube.com/@veritasium"

# c = Channel(url, proxies=proxy)

# for x in c.videos:
#     video_url = f"https://www.youtube.com/watch?v={x.video_id}"
#     #time.sleep(1)
#     try:
#         youtube.download(video_url)
#     except Exception as e:
#         print(e)
#         with open("logs.txt", "a") as file:
#             file.write(f"Error by: {x.title}   - {e}\n\n")
