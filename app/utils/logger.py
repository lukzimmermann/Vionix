import logging
import sys

class LogFilter(logging.Filter):
    def filter(self, record):
        return True
    

logger = logging.getLogger("eParts")

formatter = logging.Formatter(
    fmt = "%(asctime)s - %(levelname)s - %(message)s"
)

stream_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler('worker.log')

stream_handler.addFilter(LogFilter())

stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.handlers = [stream_handler, file_handler]

logger.setLevel(logging.INFO)