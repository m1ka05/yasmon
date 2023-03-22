from yasmon.processor import YAMLProcessor
from yasmon.tasks import TaskRunner
from yasmon.callbacks import ShellCallback
from yasmon.callbacks import CallbackSyntaxError

import unittest
import subprocess
import time


class ShellCallbackTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(ShellCallbackTest, self).__init__(*args, **kwargs)
        self.proc = YAMLProcessor()
        self.input_producer_script = 'tests/assets/watchfiles_test.sh'
        self.input_producer = None

    def start_input_producer(self):
        self.input_producer = subprocess.Popen(self.input_producer_script,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE)

        # wait a moment for  input producer (just to be safe)
        time.sleep(1)

    def stop_input_producer(self):
        if self.input_producer:
            self.input_producer.communicate()
            self.input_producer.kill()
            self.input_producer.wait()
            self.input_producer = None

    def test_from_yaml_assignment(self):
        """
        Test ShellCallback.from_yaml() for value assignment.
        """

        test_yaml = """
            type: shell
            command: somecommand
        """
        callback = ShellCallback.from_yaml('name', test_yaml)
        assert callback.name == 'name'
        assert callback.cmd == 'somecommand'

    def test_ShellCallback_raise_exceptions(self):
        """
        Test ShellCallback.from_yaml() for proper exceptions.
        """

        # general yaml error
        test_yaml = """
            type: shell
            command: ]]
        """
        fun = ShellCallback.from_yaml
        self.assertRaises(CallbackSyntaxError, fun, 'name', test_yaml)

        # command not defined
        test_yaml = """
            type: shell
        """
        fun = ShellCallback.from_yaml
        self.assertRaises(CallbackSyntaxError, fun, 'name', test_yaml)

        # command not a string
        test_yaml = """
            type: shell
            command: []
        """
        fun = ShellCallback.from_yaml
        self.assertRaises(CallbackSyntaxError, fun, 'name', test_yaml)

    def test_call_success(self):
        """
        Test ShellCallback.__call__() with stdout for success.
        """

        # stdout (command success)
        test_yaml = """
        callbacks:
            callback0:
                type: shell
                command: echo {myattr}; return 0
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
        self.start_input_producer()
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks, testenv=True)
        try:
            runner.loop.run_until_complete(runner())
        except Exception:
            self.fail()
        self.stop_input_producer()

        # stderr (command failure)
        test_yaml = """
        callbacks:
            callback0:
                type: shell
                command: echo {myattr}; return 1
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
        self.start_input_producer()
        self.proc.load_document(test_yaml)
        callbacks = self.proc.get_callbacks()
        tasks = self.proc.get_tasks(callbacks)
        runner = TaskRunner(tasks, testenv=True)
        try:
            runner.loop.run_until_complete(runner())
        except Exception:
            self.fail()
        self.stop_input_producer()


if __name__ == '__main__':
    unittest.main(verbosity=2)
