from loguru import logger
from yasmon import *
from yaml import SafeLoader, YAMLError
import argparse
from pathlib import Path

from loguru import logger
import sys


def main():
  logger.remove(0)
  journal_logger_format = (
      "<level>{level: <8}</level> | "
      "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
      "<level>{message}</level>"
  )
  logger.add(sys.stderr, format=journal_logger_format, level='DEBUG')

  parser = argparse.ArgumentParser()
  parser.add_argument("--config", type=str,
                      help="yaml config file path",
                      default=str(Path(Path.home(),'.config','yasmon','config.yaml')))
  args = parser.parse_args()

  try:
    processor = YAMLProcessor(SafeLoader)
    processor.load_file(args.config) 

    num_loggers = processor.add_loggers()
    if num_loggers > 0:
      logger.remove(1)
      logger.info(f'{num_loggers} user loggers defined. Default stderr logger removed.')
    else:
      logger.warning('no loggers configured. Defaulting to stderr logger!')

    callbacks = processor.get_callbacks()
    tasks = processor.get_tasks(callbacks)
  except (YAMLError, FileNotFoundError, OSError) as error:
    logger.error('Loading config file failed!')
    exit(1)
  except AssertionError as err:
    logger.error(f"AssertionError: {err}")
    logger.error(f"Is your config file syntax correct? Exiting!")
    exit(1)
  except NotImplementedError as err:
    logger.error(f"NotImplementedError: {err}")
    logger.error(f"Is your config file syntax correct? Exiting!")
    exit(1)
  except CallbackSyntaxError as err:
    logger.error(f"CallbackSyntaxError: {err}")
    logger.error(f"Is your config file syntax correct? Exiting!")
    exit(1)
  except Exception as err:
    logger.error(err)
    logger.error(f"Unexpected error while processing config. Exiting!")
    exit(1)
  
  runner = TaskRunner(tasks)
  runner()