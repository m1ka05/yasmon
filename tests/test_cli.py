from yasmon import cli

import unittest


class CLITest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(CLITest, self).__init__(*args, **kwargs)

    def test_parse_args_value_assignment(self):
        """
        Test cli.parse_args() for assignment of options.
        """

        config_file = 'tests/assets/cli/config.yaml'
        args = cli.parse_args('--config', config_file)
        assert args.config == config_file

    def test_execute_ExitCode_Success(self):
        """
        Test if cli.execute() returns ExitCodes.Success

        This exit code is returned in the case that no errors occured
        during operation.
        """

        args = cli.parse_args('--config', 'tests/assets/config.yaml')
        code = cli.execute(args)
        assert code == cli.ExitCodes.Success

    def test_execute_ExitCode_FileNotFoundError(self):
        """
        Test if cli.execute() returns ExitCodes.FileNotFoundError

        This exit code should be returned if the path to the config file
        does not exist.
        """

        args = cli.parse_args('--config', 'invalid/path/to/config')
        code = cli.execute(args)
        assert code == cli.ExitCodes.FileNotFoundError

    def test_execute_ExitCode_YAMLSyntaxError(self):
        """
        Test if cli.execute() returns ExitCodes.YAMLSyntaxError

        This exit code should be returned if the config syntax
        is invalid. This includes typical YAML Syntax errors as well as
        Yasmon specific syntax errors like missing callbacks and tasks.
        """
        args = cli.parse_args('--config', 'tests/assets/invalid.yaml')
        code = cli.execute(args)
        assert code == cli.ExitCodes.YAMLSyntaxError


if __name__ == '__main__':
    unittest.main(verbosity=2)
