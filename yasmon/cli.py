from yasmon.tasks import TaskRunner
from yasmon.tasks import TaskError
from yasmon.processor import YAMLProcessor
from yasmon.processor import YAMLSyntaxError
from yasmon.callbacks import CallbackSyntaxError
from yasmon.loggers import LoggerSyntaxError

from loguru import logger
import argparse
from pathlib import Path
from enum import IntEnum
import sys

logger.remove(0)


class ExitCodes(IntEnum):
    Success                         = 0  # noqa
    UnexpectedException             = 1  # noqa
    YAMLSyntaxError                 = 2  # noqa
    FileNotFoundError               = 3  # noqa
    TaskNotImplementedError         = 4  # noqa
    CallbackNotImplementedError     = 5  # noqa
    CallbackSyntaxError             = 6  # noqa
    TaskError                       = 7  # noqa
    LoggerSyntaxError               = 8  # noqa


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


def execute(args, default_logger_id):
    try:
        processor = YAMLProcessor()
        processor.load_file(args.config)

        loggers = processor.add_loggers()
        num_usr_loggers = len(loggers)
        if num_usr_loggers > 0:
            logger.remove(default_logger_id)
            logger.info(f'there are {num_usr_loggers} user loggers defined: '
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
    except LoggerSyntaxError as err:
        logger.error(f'{err.__class__.__name__}: {err}')
        return ExitCodes.LoggerSyntaxError
    except Exception as err:
        logger.error(f'Unexpected {err.__class__.__name__}: {err}')
        return ExitCodes.UnexpectedException


def main():
    default_logger_id = setup_default_logger()
    args = parse_args(*sys.argv[1:])
    return execute(args, default_logger_id)


if __name__ == '__main__':
    sys.exit(main())
