from yasmon import YAMLProcessor
from yasmon import WatchfilesTask, TaskSyntaxError
from yasmon import TaskRunner
import watchfiles
import unittest
import yaml
import subprocess
import filecmp


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

    def test_WatchfilesTask_call(self):
        test_yaml = """
        callbacks:
            copy:
                type: shell
                command: cp {path} {dest}
            touch:
                type: shell
                command: touch {target}; echo 42 > {target}
        tasks:
            addedtask:
                type: watchfiles
                changes:
                    - added
                paths:
                    - tests/assets/tmp/
                callbacks:
                    - copy
                attrs:
                    dest: tests/assets/tmp/this_was_added
            modifiedtask:
                type: watchfiles
                changes:
                    - modified
                paths:
                    - tests/assets/watchfiles_call_test
                callbacks:
                    - copy
                attrs:
                    dest: tests/assets/tmp/watchfiles_call_test
            deletedtask:
                type: watchfiles
                changes:
                    - deleted
                paths:
                    - tests/assets/watchfiles_call_test_persistent
                callbacks:
                    - touch
                attrs:
                    target: tests/assets/watchfiles_call_test_persistent
        """
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks, testenv=True)

        try:
            cmd = '''timeout 2s bash -c -- "while true; do echo $RANDOM >\
tests/assets/watchfiles_call_test; sleep 1; done;"\
echo 42 > tests/assets/tmp/added; sleep 1;\
rm tests/assets/tmp/added; rm tests/assets/watchfiles_call_test_persistent;'''
            subprocess.Popen(cmd, shell=True)
            runner.loop.run_until_complete(runner())
        except Exception:
            self.fail('Watchfiles test call failed!')

        assert filecmp.cmp(
            'tests/assets/watchfiles_call_test',
            'tests/assets/tmp/watchfiles_call_test')

        assert filecmp.cmp(
            'tests/assets/watchfiles_call_test_persistent',
            'tests/assets/tmp/this_was_added')


if __name__ == '__main__':
    unittest.main(verbosity=2)
