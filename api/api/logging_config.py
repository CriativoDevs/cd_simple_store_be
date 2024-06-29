# logging_config.py
import os

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.getenv("LOG_FILE", "debug.log"),
            "formatter": "verbose",
        },
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "DEBUG"),
            "propagate": True,
        },
    },
}
