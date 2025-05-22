import time
from pytubefix.exceptions import BotDetection, AgeRestrictedError
from app.worker.youtube.channel import YoutubeChannel
from app.worker.youtube.downloader import YoutubeDownloader
import argparse


def download_new_videos():
    while True:
        channel_handler = YoutubeChannel(enable_proxy=False)
        urls = channel_handler.get_new_video_urls()

        time_interval = 5 * 60
        start_time = 0

        for url in urls:
            start_time = time.time()
            retries = 12
            for attempt in range(1, retries + 1):
                try:
                    youtube_handler = YoutubeDownloader(enable_proxy=False)
                    youtube_handler.download(url)

                    break
                
                except BotDetection as e:
                    if attempt == retries:
                        print(f"BotDetection exception on {url}. Max retries reached. Moving to next URL.")
                        break
                    else:
                        print(f"BotDetection exception on attempt {attempt} for {url}. Waiting before retry...")
                        wait_time = 10 * 60
                        wait_step = 60
                        for i in range(int(wait_time / wait_step)):
                            print(f"Bot detection. Next try in {(wait_time / wait_step - i):.0f}min")
                            time.sleep(wait_step)

                except AgeRestrictedError as e:
                    print("Too young...")
                    break
                
                except Exception as e:
                    print(f"Exception for {url}: {e}")
                    break
                
            time_to_sleep = time_interval - (time.time() - start_time)
            if time_to_sleep > 1:
                time.sleep(time_to_sleep)
        
        time.sleep(120*60)

def transcribe():
    print("Transcribing... (this is just a placeholder)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run a specific method")
    parser.add_argument('start', choices=['download', 'transcribe'], help="Choose method to run")

    args = parser.parse_args()

    if args.start == 'download':
        download_new_videos()
    elif args.start == 'transcribe':
        transcribe()