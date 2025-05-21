import time
from pytubefix.exceptions import BotDetection, AgeRestrictedError
from app.worker.youtube.channel import YoutubeChannel
from app.worker.youtube.downloader import YoutubeDownloader

print("Start")
channel_handler = YoutubeChannel(enable_proxy=True)

urls = channel_handler.get_new_video_urls()

time_interval = 0
start_time = 0

for url in urls:
    start_time = time.time()
    print(url)
    try:
        youtube_handler = YoutubeDownloader(enable_proxy=False)
        youtube_handler.download(url)


        time_to_sleep = time_interval-(time.time()-start_time)

        if time_to_sleep > 1:
            time.sleep(time_to_sleep)
    except BotDetection as e:
        wait_time = 120*60
        wait_step = 60
        for i in range(int(wait_time/wait_step)):
            print(f"Bot detection. Next try in {(wait_time/wait_step-i):.0f}min")
            time.sleep(wait_step)

    except AgeRestrictedError as e:
        print("Too young...")
    except Exception as e:
        print(e)
