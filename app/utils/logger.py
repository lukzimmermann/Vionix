# logger.py

import logging
import traceback
from app.models import LogLevel, WorkerLog
from app.utils.database import Database

class SQLAlchemyHandler(logging.Handler):
    def emit(self, record):
        try:
            session = Database().get_session()

            exc_text = None
            if record.exc_info:
                exc_text = ''.join(traceback.format_exception(*record.exc_info))
            try:
                level_enum = LogLevel(record.levelname)
            except ValueError:
                level_enum = LogLevel.INFO

            log_entry = WorkerLog(
                level = level_enum,
                message = record.getMessage(),
                logger_name = record.name,
                filename = record.filename,
                func_name = record.funcName,
                line_no = record.lineno,
                process = record.process,
                thread = record.thread,
                exception = exc_text,
                pathname = record.pathname,
                module = record.module,
            )

            session.add(log_entry)
            session.commit()

        except Exception:
            print("Failed to log to database:", traceback.format_exc())


def get_logger(name='app_logger', level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_format = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
        console_handler.setFormatter(console_format)

        db_handler = SQLAlchemyHandler()
        db_handler.setLevel(level)

        logger.addHandler(console_handler)
        logger.addHandler(db_handler)

    return logger
