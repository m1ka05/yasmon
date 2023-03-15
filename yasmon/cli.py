from loguru import logger
from yasmon import *
from yaml import SafeLoader, YAMLError
import argparse

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("config", type=str, help="yaml config file path")
  args = parser.parse_args()

  try:
    processor = YAMLProcessor(SafeLoader)
    processor.load_file(args.config) 
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
  except Exception as err:
    logger.error(f"Unexpected error while processing config. Exiting!")
    exit(1)
  
  runner = TaskRunner(tasks)
  runner()

# TODO:
# - set logger level via cli
# - handle exceptions in async
# - refactor
# - tests
# - ci github
# - logs via mail (easy)
# - smtp callback
# - python task
# - publish