from typing import Optional
from loguru import logger

def add_logger(handler, level: Optional[str] = 'debug'):

    imp_levels = [
        'trace',
        'debug',
        'info',
        'success',
        'warning',
        'error',
        'critical'
    ]

    if level not in imp_levels:
        raise AssertionError(f"invalid logging level '{level}'")
    
    format = (
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(handler, format=format, level=level.upper())