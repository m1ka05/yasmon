from yasmon.processor import YAMLProcessor
from yasmon.tasks import WatchfilesTask, TaskSyntaxError
from yasmon.tasks import TaskError, TaskRunner, TaskList
from yasmon.callbacks import CallbackAttributeError
from yasmon.callbacks import CallbackCircularAttributeError

import watchfiles
import unittest
import time
import subprocess


class TaskRunnerTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TaskRunnerTest, self).__init__(*args, **kwargs)
        self.proc = YAMLProcessor()
        self.input_producer_script = 'tests/assets/watchfiles_test.sh'
        self.input_producer = None

    def start_input_producer(self):
        self.input_producer = subprocess.Popen(self.input_producer_script,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE)

        # wait a moment for input producer (just to be safe)
        time.sleep(1)

    def stop_input_producer(self):
        if self.input_producer:
            self.input_producer.kill()
            self.input_producer.wait()
            self.input_producer.communicate()
            self.input_producer = None

    def test_call_testenv(self):
        """
        Test TaskRunner.__call__() tasks cancel if testenv == True.
        """

        test_yaml = """
        log_stderr:
            level: error
        callbacks:
            callback0:
                type: shell
                command: exit 0;
        tasks:
            watchfilestask:
                type: watchfiles
                changes:
                    - deleted
                paths:
                    - tests/assets/tmp/
                callbacks:
                    - callback0
                attrs:
                    myattr: somevalue
        """
        self.start_input_producer()
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks, testenv=True)
        self.stop_input_producer()

        try:
            runner.loop.run_until_complete(runner())
            exited = True
        except Exception:
            raise

        assert exited is True

    def test_call_propagate_exceptions(self):
        """
        Test that TaskRunner.__call__() propagates exceptions.
        """

        # TaskError
        test_yaml = """
        callbacks:
            callback0:
                type: shell
                command: exit 0
        tasks:
            watchfilestask:
                type: watchfiles
                changes:
                    - added
                    - modified
                    - deleted
                paths:
                    - file/not/found
                callbacks:
                    - callback0
                max_retry: 1
                timeout: 1
        """
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks)
        fun = runner.loop.run_until_complete
        self.assertRaises(TaskError, fun, runner())

        # CallbackCircularAttributeError
        test_yaml = """
        callbacks:
            callback0:
                type: shell
                command: exit 0; {WRONG}
        tasks:
            watchfilestask:
                type: watchfiles
                changes:
                    - modified
                paths:
                    - tests/assets/tmp/watchfiles_call_test
                callbacks:
                    - callback0
                attrs:
                    myattr: somevalue using {WRONG}
                    WRONG: "{myattr}"
        """
        self.start_input_producer()
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks, testenv=True)
        fun = runner.loop.run_until_complete
        self.assertRaises(CallbackCircularAttributeError, fun, runner())
        self.stop_input_producer()

        # CallbackAttributesError
        test_yaml = """
        callbacks:
            callback0:
                type: shell
                command: exit 0; {WRONG}
        tasks:
            watchfilestask:
                type: watchfiles
                changes:
                    - added
                paths:
                    - tests/assets/tmp/
                callbacks:
                    - callback0
                attrs:
                    myattr: somevalue
        """
        self.start_input_producer()
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks, testenv=True)
        fun = runner.loop.run_until_complete
        self.assertRaises(CallbackAttributeError, fun, runner())
        self.stop_input_producer()

        # TaskError
        test_yaml = """
        callbacks:
            callback0:
                type: shell
                command: exit 0;
        tasks:
            watchfilestask:
                type: watchfiles
                changes:
                    - added
                    - deleted
                    - modified
                paths:
                    - tests/assets/tmp/DOES_NOT_EXIST
                callbacks:
                    - callback0
                max_retry: 1
                timeout: 1
        """
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks)
        fun = runner.loop.run_until_complete
        self.assertRaises(TaskError, fun, runner())


class WatchfilesTaskTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(WatchfilesTaskTest, self).__init__(*args, **kwargs)
        self.proc = YAMLProcessor()
        self.input_producer_script = 'tests/assets/watchfiles_test.sh'
        self.input_producer = None

    def start_input_producer(self):
        self.input_producer = subprocess.Popen(self.input_producer_script,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE)

        # wait a moment for input producer (just to be safe)
        time.sleep(1)

    def stop_input_producer(self):
        if self.input_producer:
            self.input_producer.kill()
            self.input_producer.wait()
            self.input_producer.communicate()
            self.input_producer = None

    def test_from_yaml_value_assignment(self):
        """
        Test WatchfilesTask.from_yaml() for assignment of values.
        """

        # default values
        data = """
        changes:
            - added
            - modified
            - deleted
        paths:
            - tests/assets/config.yaml
            - tests/assets/invalid.yaml
        """
        task = WatchfilesTask.from_yaml("name", data, [])
        assert task.name == 'name'
        assert task.paths == [
            'tests/assets/config.yaml',
            'tests/assets/invalid.yaml'
        ]
        assert task.changes == [
            watchfiles.Change.added,
            watchfiles.Change.modified,
            watchfiles.Change.deleted
        ]
        assert task.attrs == {}
        assert task.timeout == 30
        assert task.max_retry == 5

        # fully specified
        data = """
        changes:
            - added
            - modified
            - deleted
        paths:
            - tests/assets/config.yaml
            - tests/assets/invalid.yaml
        attrs:
            myattr1: value1
            myattr2: value2
        timeout: 10
        max_retry: 7
        """
        task = WatchfilesTask.from_yaml("name", data, [])
        assert task.name == 'name'
        assert task.paths == [
            'tests/assets/config.yaml',
            'tests/assets/invalid.yaml'
        ]
        assert task.changes == [
            watchfiles.Change.added,
            watchfiles.Change.modified,
            watchfiles.Change.deleted
        ]
        assert task.attrs == {
            'myattr1': 'value1',
            'myattr2': 'value2',
        }
        assert task.timeout == 10
        assert task.max_retry == 7

    def test_from_yaml_raise_TaskSyntaxError(self):
        """
        Test if WatchfilesTask.from_yaml() raises TaskSyntaxError
        """
        fun = WatchfilesTask.from_yaml

        # general yaml syntax error
        data = """
        changes:
            - added
            - modified
            - deleted
        paths: ][
        attrs:
            myattr1: value1
            myattr2: value2
        """
        self.assertRaises(TaskSyntaxError, fun, "name", data, [])

        # missing changes dictionary
        data = """
        paths:
            - some/path
        attrs:
            myattr1: value1
            myattr2: value2
        """
        self.assertRaises(TaskSyntaxError, fun, "name", data, [])

        # missing paths dictionary
        data = """
        changes:
            - added
            - modified
            - deleted
        attrs:
            myattr1: value1
            myattr2: value2
        """
        self.assertRaises(TaskSyntaxError, fun, "name", data, [])

        # empty paths dictionary
        data = """
        changes:
            - added
            - modified
            - deleted
        paths:
        attrs:
            myattr1: value1
            myattr2: value2
        """
        self.assertRaises(TaskSyntaxError, fun, "name", data, [])

        # empty paths list
        data = """
        changes:
            - added
            - modified
            - deleted
        paths: []
        attrs:
            myattr1: value1
            myattr2: value2
        """
        self.assertRaises(TaskSyntaxError, fun, "name", data, [])

        # paths is not a list
        data = """
        changes:
            - added
            - modified
            - deleted
        paths:
            /some/path1:
            /some/path2:
        attrs:
            myattr1: value1
            myattr2: value2
        """
        self.assertRaises(TaskSyntaxError, fun, "name", data, [])

        # paths is not a string
        data = """
        changes:
            - added
            - modified
            - deleted
        paths:
            - []
        attrs:
            myattr1: value1
            myattr2: value2
        """
        self.assertRaises(TaskSyntaxError, fun, "name", data, [])

        # changes is not a list
        data = """
        changes:
            added:
            modified:
            deleted:
        paths:
            - tests/assets/config.yaml
            - tests/assets/invalid.yaml
        attrs:
            myattr1: value1
            myattr2: value2
        """
        self.assertRaises(TaskSyntaxError, fun, "name", data, [])

        # attrs not a dictionary
        data = """
        changes:
            - added
            - modified
            - deleted
        paths:
            - tests/assets/config.yaml
            - tests/assets/invalid.yaml
        attrs:
            - myattr1: value1
            - myattr2: value2
        """
        self.assertRaises(TaskSyntaxError, fun, "name", data, [])

        # changes values invalid
        data = """
        changes:
            - added
            - INVALID
            - deleted
        paths:
            - tests/assets/config.yaml
            - tests/assets/invalid.yaml
        attrs:
            myattr1: value1
            myattr2: value2
        """
        self.assertRaises(TaskSyntaxError, fun, "name", data, [])

        # invalid max_retry (due to ValueError)
        data = """
        changes:
            - added
            - deleted
        paths:
            - tests/assets/config.yaml
            - tests/assets/invalid.yaml
        attrs:
            myattr1: value1
            myattr2: value2
        max_retry: INVALID
        """
        self.assertRaises(TaskSyntaxError, fun, "name", data, [])

        # invalid max_retry (due to TypeError)
        data = """
        changes:
            - added
            - deleted
        paths:
            - tests/assets/config.yaml
            - tests/assets/invalid.yaml
        attrs:
            myattr1: value1
            myattr2: value2
        max_retry:
            INVALID:
        """
        self.assertRaises(TaskSyntaxError, fun, "name", data, [])

        # invalid timeout (due to ValueError)
        data = """
        changes:
            - added
            - deleted
        paths:
            - /some/path1
            - /some/path2
        attrs:
            myattr1: value1
            myattr2: value2
        timeout: INVALID
        """
        self.assertRaises(TaskSyntaxError, fun, "name", data, [])

        # invalid timeout (due to TypeError)
        data = """
        changes:
            - added
            - deleted
        paths:
            - tests/assets/config.yaml
            - tests/assets/invalid.yaml
        attrs:
            myattr1: value1
            myattr2: value2
        timeout:
            - INVALID
        """
        self.assertRaises(TaskSyntaxError, fun, "name", data, [])

        # invalid timeout (must be positive)
        data = """
        changes:
            - added
            - deleted
        paths:
            - tests/assets/config.yaml
            - tests/assets/invalid.yaml
        attrs:
            myattr1: value1
            myattr2: value2
        timeout: 0
        """
        self.assertRaises(TaskSyntaxError, fun, "name", data, [])

    def test_call_testenv(self):
        """
        Test if WatchfilesTask.__call__() runs through.
        """

        # TaskError on watched file deleted
        test_yaml = """
        callbacks:
            callback0:
                type: shell
                command: exit 0;
        tasks:
            watchfilestask:
                type: watchfiles
                changes:
                    - modified
                    - deleted
                    - added
                paths:
                    - tests/assets/tmp/
                callbacks:
                    - callback0
                max_retry: 2
                timeout: 1
        """
        self.start_input_producer()
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks, testenv=True)
        fun = runner.loop.run_until_complete
        try:
            fun(runner())
        except Exception:
            self.fail()
        self.stop_input_producer()

    def test_call_raise_exceptions(self):
        """
        Test if WatchfilesTask.__call__() raises TaskError.
        """

        # TaskError on watched file deleted
        test_yaml = """
        callbacks:
            callback0:
                type: shell
                command: exit 0;
        tasks:
            watchfilestask:
                type: watchfiles
                changes:
                    - modified
                paths:
                    - tests/assets/tmp/watchfiles_test.sh.pid
                callbacks:
                    - callback0
                max_retry: 2
                timeout: 1
        """
        self.start_input_producer()
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks)
        fun = runner.loop.run_until_complete
        self.assertRaises(TaskError, fun, runner())
        self.stop_input_producer()


class TaskListTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TaskListTest, self).__init__(*args, **kwargs)

    def test_construction(self):
        """
        Test TaskList.__init__().
        """

        data = """
        changes:
            - added
        paths:
            - /
        """
        task = WatchfilesTask.from_yaml("name", data, [])

        # empty task list
        tasklist = TaskList()
        assert len(tasklist) == 0

        # taskl list form an iterable
        tasklist = TaskList([task, task, task])
        assert len(tasklist) == 3


if __name__ == '__main__':
    unittest.main(verbosity=2)
