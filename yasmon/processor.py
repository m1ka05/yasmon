from loguru import logger
from systemd.journal import JournalHandler
import yaml
import sys
from .callbacks import AbstractCallback, CallbackDict, ShellCallback, LoggerCallback, CallbackSyntaxError
from .tasks import TaskList, WatchfilesTask
from .utils import add_logger


class YAMLProcessor:
    def __init__(self, loader):
        self.loader = loader
        self.data = None

    def load_file(self, filename: str):
        try:
            fh = open(filename, "r")
            logger.info(f'using config file {filename}')
        except FileNotFoundError as err:
            logger.error(f"YAML file {filename} not found")
            raise err
        except OSError as err:
            logger.error(f"OSError while opening {filename}")
            raise err
        except Exception as err:
            logger.error(f"Unexpected error while opening {filename}")
            raise err
        else:
            try:
                self.data = yaml.load(fh, Loader=self.loader)
            except yaml.YAMLError as err:
                if hasattr(err, 'problem_mark'):
                    mark = getattr(err, 'problem_mark')
                    problem = getattr(err, 'problem')
                    message = f'YAML problem in line {mark.line} column {mark.column}:\n {problem})'
                elif hasattr(err, 'problem'):
                    problem = getattr(err, 'problem')
                    message = f'YAML problem:\n {problem}'
                logger.error(message)
                raise err
            finally:
                fh.close()
    
    def add_loggers(self) -> int:
        """
        Add defined loggers.

        :return: number of added loggers
        :rtype: int
        """
        logger.info(f'processing loggers...')
        loggers = []

        if 'log_stderr' in self.data:
            data = self.data['log_stderr']
            if type(data) is not dict:
                loggers.append((sys.stderr, None))
            elif 'level' in data:
                loggers.append((sys.stderr, data['level']))
            
        if 'log_file' in self.data:
            data = self.data['log_file']
            if type(data) is not dict:
                raise AssertionError(f'log_file data must be a dictionary and contain a path key!')
            elif 'level' in data:
                loggers.append((data['path'], data['level']))
            else:
                loggers.append((data['path'], None))
            
        if 'log_journal' in self.data:
            data = self.data['log_journal']
            if type(data) is not dict:
                loggers.append((JournalHandler(), None))
            elif 'level' in data:
                loggers.append((JournalHandler(), data['level']))


        for (log, level) in loggers:
            if level is None:
                add_logger(log)
            else:
                add_logger(log, level=level)
        
        return len(loggers)

    def load_document(self, document: str):
        try:
            self.data = yaml.safe_load(document)
            logger.info(f'config:\n{document}')
        except yaml.YAMLError as err:
            if hasattr(err, 'problem_mark'):
                mark = getattr(err, 'problem_mark')
                problem = getattr(err, 'problem')
                message = f'YAML problem in line {mark.line} column {mark.column}:\n {problem})'
            elif hasattr(err, 'problem'):
                problem = getattr(err, 'problem')
                message = f'YAML problem:\n {problem}'
            logger.error(message)
            raise err

    def get_tasks(self, callbacks: CallbackDict):
        logger.debug(f'processing tasks...')
        if 'tasks' not in self.data:
            raise AssertionError('tasks not defined')

        tasks = self.data['tasks']
        
        if type(tasks) is not dict:
            raise AssertionError('tasks must be a dictionary')

        taskslist = TaskList()
        for task in tasks:
            taskdata = tasks[task]
            if type(taskdata) is not dict:
                raise AssertionError(f'{task} task data must be a dictionary')

            taskdata_yaml = yaml.dump(taskdata)
            task_callbacks: list[AbstractCallback] = [
                callbacks[c] for c in taskdata["callbacks"] if c in taskdata["callbacks"]
            ]

            match taskdata['type']:
                case 'watchfiles':
                    taskslist.append(WatchfilesTask.from_yaml(task, taskdata_yaml, task_callbacks))
                case _:
                    raise NotImplementedError(f'task type {taskdata["type"]} not implement')

        logger.debug(f'done processing tasks')
        return taskslist

    def get_callbacks(self):
        logger.debug(f'processing callbacks...')
        if 'callbacks' not in self.data:
            raise AssertionError('callbacks not defined')
        
        callbacks = self.data['callbacks']
        
        if type(self.data['callbacks']) is not dict:
            raise AssertionError('callbacks must be a dictionary')

        callbacksdict = CallbackDict()
        for callback in callbacks:
            callbackdata = self.data['callbacks'].get(callback)
            if type(callbackdata) is not dict:
                raise AssertionError(f'{callback} callback data must be a dictionary')

            try:
                match callbackdata['type']:
                    case 'shell':
                        callbacksdict[callback] = ShellCallback.from_yaml(callback, yaml.dump(callbackdata))
                    case 'logger':
                        callbacksdict[callback] = LoggerCallback.from_yaml(callback, yaml.dump(callbackdata))
                    case _:
                        raise NotImplementedError(f'callback type {callbackdata["type"]} not implement')
            except CallbackSyntaxError as err:
                logger.error(f'error while processing callbacks: {err}. Exiting!')


        logger.debug(f'done processing callbacks')
        return callbacksdict