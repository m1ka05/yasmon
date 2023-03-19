from yasmon import YAMLProcessor
from yasmon import WatchfilesTask, TaskSyntaxError
from yasmon import TaskRunner
from yasmon import CallbackAttributeError
from yasmon import CallbackCircularAttributeError
import watchfiles
import unittest
import yaml


class WatchfilesTaskTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(WatchfilesTaskTest, self).__init__(*args, **kwargs)
        self.proc = YAMLProcessor(yaml.SafeLoader)

    def test_from_yaml(self):
        data = """
        changes:
            - added
            - modified
            - deleted
        paths:
            - /some/path1
            - /some/path2
        attrs:
            myattr1: value1
            myattr2: value2
        """
        task = WatchfilesTask.from_yaml("name", data, [])
        assert task.name == 'name'
        assert task.paths == ['/some/path1', '/some/path2']
        assert task.changes == [
            watchfiles.Change.added,
            watchfiles.Change.modified,
            watchfiles.Change.deleted
        ]
        assert task.attrs == {
            'myattr1': 'value1',
            'myattr2': 'value2',
        }

    def test_from_yaml_invalid_yaml_syntax(self):
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
        self.assertRaises(yaml.YAMLError,
                          WatchfilesTask.from_yaml, "name", data, [])

    def test_from_yaml_raises_TaskSyntaxError_missing_changes(self):
        data = """
        paths:
            - some/path
        attrs:
            myattr1: value1
            myattr2: value2
        """
        self.assertRaises(TaskSyntaxError,
                          WatchfilesTask.from_yaml, "name", data, [])

    def test_from_yaml_raises_TaskSyntaxError_missing_paths(self):
        data = """
        changes:
            - added
            - modified
            - deleted
        attrs:
            myattr1: value1
            myattr2: value2
        """
        self.assertRaises(TaskSyntaxError,
                          WatchfilesTask.from_yaml, "name", data, [])

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
        self.assertRaises(TaskSyntaxError,
                          WatchfilesTask.from_yaml, "name", data, [])

    def test_from_yaml_raises_TaskSyntaxError_paths_empty_list(self):
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
        self.assertRaises(TaskSyntaxError,
                          WatchfilesTask.from_yaml, "name", data, [])

    def test_from_yaml_raises_TaskSyntaxError_paths_not_list(self):
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
        self.assertRaises(TaskSyntaxError,
                          WatchfilesTask.from_yaml, "name", data, [])

    def test_from_yaml_raises_TaskSyntaxError_changes_not_list(self):
        data = """
        changes:
            added:
            modified:
            deleted:
        paths:
            - /some/path1
            - /some/path2
        attrs:
            myattr1: value1
            myattr2: value2
        """
        self.assertRaises(TaskSyntaxError,
                          WatchfilesTask.from_yaml, "name", data, [])

    def test_from_yaml_raises_TaskSyntaxError_attrs_not_dict(self):
        data = """
        changes:
            - added
            - modified
            - deleted
        paths:
            - /some/path1
            - /some/path2
        attrs:
            - myattr1: value1
            - myattr2: value2
        """
        self.assertRaises(TaskSyntaxError,
                          WatchfilesTask.from_yaml, "name", data, [])

    def test_from_yaml_raises_TaskSyntaxError_invalid_change(self):
        data = """
        changes:
            - added
            - INVALID
            - deleted
        paths:
            - /some/path1
            - /some/path2
        attrs:
            myattr1: value1
            myattr2: value2
        """
        self.assertRaises(TaskSyntaxError,
                          WatchfilesTask.from_yaml, "name", data, [])

    def test_TaskRunner_call_propagate_exception(self):
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
        """
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks)

        self.assertRaises(
            FileNotFoundError,
            runner.loop.run_until_complete,
            runner())

    def test_TaskRunner_call_test_testenv(self):
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
                    - tests/assets/tmp/watchfiles_call_test
                callbacks:
                    - callback0
                attrs:
                    myattr: somevalue
        """
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks, testenv=True)

        try:
            runner.loop.run_until_complete(runner())
        except Exception:
            raise

    def test_TaskRunner_call_test_circular_attrs(self):
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
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks, testenv=True)

        self.assertRaises(
            CallbackCircularAttributeError,
            runner.loop.run_until_complete,
            runner())

    def test_TaskRunner_call_test_invalid_attr(self):
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
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks, testenv=True)

        self.assertRaises(
            CallbackAttributeError,
            runner.loop.run_until_complete,
            runner())


if __name__ == '__main__':
    unittest.main(verbosity=2)
