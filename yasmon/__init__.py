from .processor import YAMLProcessor
from .callbacks import AbstractCallback, CallbackDict, ShellCallback, LoggerCallback
from .callbacks import CallbackAttributeError, CallbackCircularAttributeError
from .callbacks import CallbackSyntaxError
from .callbacks import process_attributes
from .tasks import AbstractTask, TaskList, WatchfilesTask, TaskRunner
from .cli import main

from loguru import logger
from systemd.journal import JournalHandler

logger.remove(0)
journal_logger_format = (
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)
logger.add(JournalHandler(), format=journal_logger_format)

__all__ = [
    'YAMLProcessor',
    'AbstractCallback',
    'CallbackDict',
    'ShellCallback',
    'LoggerCallback',
    'AbstractTask',
    'TaskList',
    'WatchfilesTask',
    'TaskRunner',
    'CallbackAttributeError',
    'CallbackCircularAttributeError',
    'CallbackSyntaxError',
    'process_attributes',
    'main',
]

__name__ = 'yasmon'
