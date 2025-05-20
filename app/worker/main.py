from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import time

from app.worker.youtube.channel import YoutubeChannel
from app.worker.youtube.downloader import YoutubeDownloader

# class Scanner():
#     def __init__(self):
#         self.is_running = False

#     def start_scan(self):
#         if not self.is_running:
#             try:
#                 self.is_running = True
#                 y = YoutubeDownloader()
#                 y.download("https://www.youtube.com/watch?v=AeJ9q45PfD0")
#             except Exception as e:
#                 pass
#             finally: 
#                 self.is_running = False

# scanner = Scanner()

# scheduler = BackgroundScheduler()
# scheduler.add_job(
#     scanner.start_scan,
#     trigger='cron',
#     # minute='*',
#     hour=2,
#     minute=0,
#     next_run_time=datetime.now())

# scheduler.start()

# try:
#     while True:
#         time.sleep(0.1)
# except (KeyboardInterrupt, SystemExit):
#     scheduler.shutdown()

print("Start")
channel_handler = YoutubeChannel(enable_proxy=True)

urls = channel_handler.get_new_video_urls()

for url in urls[:20]:
    print(url)
    youtube_handler = YoutubeDownloader(enable_proxy=True)
    youtube_handler.download(url)
