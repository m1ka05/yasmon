from yasmon.tasks import TaskRunner
from yasmon.tasks import TaskError
from yasmon.processor import YAMLProcessor
from yasmon.processor import YAMLSyntaxError
from yasmon.callbacks import CallbackSyntaxError
from yasmon.loggers import LoggerSyntaxError

from loguru import logger
import argparse
from pathlib import Path
import asyncio
from enum import IntEnum
import sys

logger.remove(0)


class ExitCodes(IntEnum):
    Success                         = 0  # noqa
    Exception                       = 1  # noqa
    YAMLSyntaxError                 = 2  # noqa
    FileNotFoundError               = 3  # noqa
    OSError                         = 4  # noqa
    AssertionError                  = 5  # noqa
    TaskNotImplementedError         = 6  # noqa
    CallbackNotImplementedError     = 7  # noqa
    CallbackSyntaxError             = 8  # noqa
    TaskError                       = 9  # noqa
    CancelledError                  = 10 # noqa
    LoggerSyntaxError               = 11 # noqa


def parse_args(*args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str,
                        help="yaml config file path",
                        default=str(Path(Path.home(),
                                         '.config',
                                         'yasmon',
                                         'config.yaml')))
    return parser.parse_args(args)


def setup_default_logger():
    journal_logger_format = (
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    return logger.add(sys.stderr, format=journal_logger_format, level='DEBUG')


def execute(args):
    try:
        processor = YAMLProcessor()
        processor.load_file(args.config)

        loggers = processor.add_loggers()
        num_loggers = len(loggers)
        if num_loggers > 0:
            logger.remove(1)
            logger.info(f'there are {num_loggers} user loggers defined: '
                        'default stderr logger removed')
        else:
            logger.warning('there are no user loggers defined: '
                           'keeping default stderr logger')

        callbacks = processor.get_callbacks()
        tasks = processor.get_tasks(callbacks)
        runner = TaskRunner(tasks)
        runner.loop.run_until_complete(runner())
        return ExitCodes.Success
    except YAMLSyntaxError as err:
        logger.error(f'{err.__class__.__name__}: {err}')
        return ExitCodes.YAMLSyntaxError
    except FileNotFoundError as err:
        logger.error(f'{err.__class__.__name__}: {err}')
        return ExitCodes.FileNotFoundError
    except CallbackSyntaxError as err:
        logger.error(f'{err.__class__.__name__}: {err}')
        return ExitCodes.CallbackSyntaxError
    except TaskError as err:
        logger.error(f'{err.__class__.__name__}: {err}')
        return ExitCodes.TaskError
    except asyncio.CancelledError as err:
        logger.error(f'{err.__class__.__name__}: {err}')
        return ExitCodes.CancelledError
    except LoggerSyntaxError as err:
        logger.error(f'{err.__class__.__name__}: {err}')
        return ExitCodes.LoggerSyntaxError
    except OSError as err:
        logger.error(f'{err.__class__.__name__}: {err}')
        return ExitCodes.OSError
    except AssertionError as err:
        logger.error(f'{err.__class__.__name__}: {err}')
        return ExitCodes.AssertionError
    except NotImplementedError as err:
        logger.error(f'{err.__class__.__name__}: {err}')
        return ExitCodes.AssertionError
    except Exception as err:
        logger.error(f'{err.__class__.__name__}: {err}')
        return ExitCodes.Exception


def main():
    setup_default_logger()
    args = parse_args(*sys.argv[1:])
    return execute(args)


if __name__ == '__main__':
    sys.exit(main())
