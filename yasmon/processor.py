from yasmon.callbacks import AbstractCallback
from yasmon.callbacks import CallbackDict
from yasmon.callbacks import ShellCallback, LoggerCallback, CallbackSyntaxError
from yasmon.callbacks import CallbackNotImplementedError
from yasmon.tasks import TaskList, WatchfilesTask, TaskNotImplementedError
from yasmon.loggers import LoggerSyntaxError, AbstractLogger
from yasmon.loggers import StdErrLogger, FileLogger, JournalLogger

from loguru import logger
import yaml


class YAMLSyntaxError(Exception):
    """
    Raised when on general YAML syntax errors.
    """

    def __init__(self, message="yaml syntax error"):
        self.message = message
        super().__init__(self.message)


class YAMLProcessor:
    def __init__(self):
        self.data = None

    def load_file(self, filename: str):
        try:
            fh = open(filename, "r")
            logger.info(f'using config file {filename}')
        except FileNotFoundError as err:
            logger.error(f"YAML file {filename} not found")
            raise err
        except PermissionError as err:
            logger.error(
                f"{err.__class__.__name__} while opening {filename} {err}")
            raise err
        except OSError as err:
            logger.error(
                f"{err.__class__.__name__} while opening {filename} {err}")
            raise err
        except Exception as err:
            logger.error(
                f"{err.__class__.__name__} while opening {filename} {err}")
            raise err
        else:
            try:
                self.data = yaml.safe_load(fh)
            except yaml.YAMLError as err:
                raise YAMLSyntaxError(err)
            finally:
                fh.close()

            if self.data is None:
                raise YAMLSyntaxError('config file is empty')

    def add_loggers(self) -> list[AbstractLogger]:
        """
        Add defined loggers.

        :return: list of added loggers or empty list
        :rtype: list[AbstractLogger]
        """
        logger.info('processing loggers...')
        loggers: list[AbstractLogger] = []

        for key in self.data:
            data = self.data[key]
            yaml_data = yaml.dump(data)
            try:
                match key:
                    case 'log_stderr':
                        instance = StdErrLogger.from_yaml(yaml_data)
                        loggers.append(instance)
                    case 'log_file':
                        instance = FileLogger.from_yaml(yaml_data)
                        loggers.append(instance)
                    case 'log_journal':
                        instance = JournalLogger.from_yaml(yaml_data)
                        loggers.append(instance)
            except LoggerSyntaxError:
                raise

        return loggers

    def load_document(self, document: str):
        try:
            self.data = yaml.safe_load(document)
            logger.info(f'config:\n{document}')
        except yaml.YAMLError as err:
            raise YAMLSyntaxError(err)

        if self.data is None:
            raise YAMLSyntaxError('config document is empty')

    def get_tasks(self, callbacks: CallbackDict):
        logger.debug('processing tasks...')
        if 'tasks' not in self.data:
            raise YAMLSyntaxError('tasks not defined')

        if not self.data['tasks']:
            logger.warning('no tasks defined')
            return TaskList()

        tasks = self.data['tasks']

        if type(tasks) is not dict:
            raise YAMLSyntaxError('tasks must be a dictionary')

        taskslist = TaskList()
        for task in tasks:
            taskdata = tasks[task]
            if type(taskdata) is not dict:
                raise YAMLSyntaxError(f'{task} task data must be a dictionary')

            taskdata_yaml = yaml.dump(taskdata)

            if 'callbacks' not in taskdata:
                raise YAMLSyntaxError(f'{task} task data must include'
                                      ' callbacks list')

            task_callbacks: list[AbstractCallback] = [
                callbacks[c] for c in taskdata["callbacks"]
                if c in taskdata["callbacks"]
            ]

            match taskdata['type']:
                case 'watchfiles':
                    taskslist.append(WatchfilesTask.from_yaml(task,
                                                              taskdata_yaml,
                                                              task_callbacks))
                case _:
                    raise TaskNotImplementedError(
                        f'task type {taskdata["type"]}'
                        ' not implement')

        logger.debug('done processing tasks')
        return taskslist

    def get_callbacks(self):
        logger.debug('processing callbacks...')
        if 'callbacks' not in self.data:
            raise YAMLSyntaxError('callbacks not defined')

        if not self.data['callbacks']:
            logger.warning('no callbacks defined')
            return

        callbacks = self.data['callbacks']

        if type(self.data['callbacks']) is not dict:
            raise YAMLSyntaxError('callbacks must be a dictionary')

        callbacksdict = CallbackDict()
        for callback in callbacks:
            callbackdata = self.data['callbacks'].get(callback)
            if type(callbackdata) is not dict:
                raise YAMLSyntaxError(f'{callback} callback data must'
                                      ' be a dictionary')

            try:
                match callbackdata['type']:
                    case 'shell':
                        callbacksdict[callback] = ShellCallback.from_yaml(
                            callback, yaml.dump(callbackdata))
                    case 'logger':
                        callbacksdict[callback] = LoggerCallback.from_yaml(
                            callback, yaml.dump(callbackdata))
                    case _:
                        raise CallbackNotImplementedError(
                            f'callback type {callbackdata["type"]} '
                            'not implement')
            except CallbackSyntaxError as err:
                logger.error(f'error while processing callbacks: {err}. '
                             'Exiting!')
                raise err

        logger.debug('done processing callbacks')
        return callbacksdict
