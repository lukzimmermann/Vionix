from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import time

class Scanner():
    def __init__(self):
        self.is_running = False

    def start_scan(self):
        if not self.is_running:
            try:
                self.is_running = True
                print(f"Start @ {datetime.now()}")
                time.sleep(5)
                print(f"End @ {datetime.now()}")
            except Exception as e:
                pass
            finally: 
                self.is_running = False

scanner = Scanner()

scheduler = BackgroundScheduler()
scheduler.add_job(
    scanner.start_scan,
    trigger='cron',
    minute='*',
    # hour=2,
    # minute=0,
    next_run_time=datetime.now())

scheduler.start()

try:
    while True:
        time.sleep(0.1)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()