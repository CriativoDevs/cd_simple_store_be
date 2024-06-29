import logging
from .models import LogEntry


class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = LogEntry(
            level=record.levelname,
            message=record.getMessage(),
            module=record.module,
        )
        log_entry.save()
