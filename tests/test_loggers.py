from yasmon.processor import YAMLProcessor
from yasmon.loggers import LoggerSyntaxError
from yasmon.loggers import JournalLogger
from yasmon.loggers import StdErrLogger
from yasmon.loggers import FileLogger

import unittest


class JournalLoggerTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(JournalLoggerTest, self).__init__(*args, **kwargs)
        self.proc = YAMLProcessor()

    def test_from_yaml_raise_exceptions(self):
        """
        Test if JournalLogger.from_yaml() raises appropriate exceptions.
        """

        data = """
        level: ]]
        """
        self.assertRaises(LoggerSyntaxError, JournalLogger.from_yaml, data)


class StdErrLoggerTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(StdErrLoggerTest, self).__init__(*args, **kwargs)
        self.proc = YAMLProcessor()

    def test_from_yaml_raise_exceptions(self):
        """
        Test if StdErrLogger.from_yaml() raises appropriate exceptions.
        """

        data = """
        level: ]]
        """
        self.assertRaises(LoggerSyntaxError, StdErrLogger.from_yaml, data)


class FileLoggerTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(FileLoggerTest, self).__init__(*args, **kwargs)
        self.proc = YAMLProcessor()

    def test_from_yaml_raise_exceptions(self):
        """
        Test if FileLogger.from_yaml() raises appropriate exceptions.
        """

        data = """
        level: ]]
        """
        self.assertRaises(LoggerSyntaxError, FileLogger.from_yaml, data)

        data = """
        level: info
        path:
            - /invalid/syntax
        """
        self.assertRaises(LoggerSyntaxError, FileLogger.from_yaml, data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
