from loguru import logger
import yaml
from .callbacks import AbstractCallback, CallbackDict, ShellCallback
from .tasks import TaskList, WatchfilesTask


class YAMLProcessor:
    def __init__(self, loader):
        self.loader = loader
        self.data = None

    def load_file(self, filename: str):
        try:
            fh = open(filename, "r")
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

    def load_document(self, document: str):
        try:
            self.data = yaml.safe_load(document)
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

        return taskslist

    def get_callbacks(self):
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

            match callbackdata['type']:
                case 'shell':
                    callbacksdict[callback] = ShellCallback.from_yaml(callback, yaml.dump(callbackdata))
                case _:
                    raise NotImplementedError(f'callback type {callbackdata["type"]} not implement')

        return callbacksdict