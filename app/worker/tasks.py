from os import name
from celery import Celery, chain
import time
from celery.schedules import crontab
from app.worker.youtube.downloader import YoutubeDownloader
from app.worker.transcribtion import Transcription

import redis

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Flush all databases (use .flushdb() to clear just the current one)
r.flushall()

print("All clear...")

app = Celery("tasks", broker="redis://localhost:6379", backend="redis://localhost:6379")
app.autodiscover_tasks(['app.worker.youtube', 'app.worker.transcribtion', 'app.worker.tasks'])

app.conf.beat_schedule = {
    'check-new-videos-every-5-minutes': {
        'task': 'app.worker.tasks.check_new_videos',
        'schedule': crontab(minute='*/20'),
    },
}
app.conf.timezone = 'UTC'

@app.task()
def check_new_videos():
    for i in range(10):
        print(f"Queueing download task {i}")
        download.delay(str(i))


@app.task(rate_limit='3/h')
def download(video_url):
    time.sleep(4)
    print(f"download finished {video_url}...")
    transcribe.delay(str(video_url))
    #downloader = YoutubeDownloader()
    #video_id = downloader.download(video_url)
    #transcribe(video_id)

@app.task()
def transcribe(video_id):
    print(f"transcribe {video_id}...")
    time.sleep(4)
    #transcription = Transcription()
    #transcription.transcribe(video_id)