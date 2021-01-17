# -*- coding: utf-8 -*-
# pylint: disable=import-error

"""Module contains base classes and methods available for all testing."""

from __future__ import print_function, absolute_import

# Standard modules
import io
import os
import shutil
import sys
import textwrap

# Installed packages
import unittest2

# Target package for testing
from yamlfig import YamlConfigParser, ParseError

# Globals
TESTDIR_BASE = os.path.abspath('tmp-testdirs')


# Helper functions
def _as_naive_datetime_in_utc(tzdatetime):
    """Transform an offset-aware datetime into a naive one in UTC/Zulu."""
    return tzdatetime.replace(tzinfo=None) - tzdatetime.utcoffset()


class CaptureIO(object):
    """Redirect IO to a buffer to test the output of a code block.

    The typical pattern would wrap the target activity within a with
    block, and then test what was written to stdout or stderr at
    the end:

    with CaptureIO(filepfx) as capio:
      do_some_stuff()
      print_some_stuff()
      maybe_raise_an_exception()

    stdout_txt = capio.get_stdout()
    stderr_txt = capio.get_stderr()
    """

    # pylint: disable=useless-object-inheritance

    def __init__(self, filepfx):
        """Construct stdout/err buffers to capture them."""
        self.orig_stdout = None
        self.orig_stderr = None

        self.stdout_file = '{0}.out'.format(filepfx)
        self.stderr_file = '{0}.err'.format(filepfx)

        self.stdout = None
        self.stderr = None

    def __enter__(self):
        """Redirect stdout/err to the object buffers."""
        # pylint: disable=consider-using-with
        assert self.orig_stdout is None
        assert self.orig_stderr is None
        self.orig_stdout = sys.stdout
        self.orig_stderr = sys.stderr

        self.stdout = io.open(self.stdout_file, 'w')
        self.stderr = io.open(self.stderr_file, 'w')

        sys.stdout = self.stdout
        sys.stderr = self.stderr

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Restore stdout/err to their pre-redirection values."""
        self.stdout.close()
        self.stderr.close()
        sys.stdout = self.orig_stdout
        sys.stderr = self.orig_stderr
        self.orig_stdout = None
        self.orig_stderr = None

    def get_stdout(self):
        """Return the captured standard output as a string."""
        with io.open(self.stdout_file, 'r') as handle:
            return handle.read()

    def get_stderr(self):
        """Return the captured standard error as a string."""
        with io.open(self.stderr_file, 'r') as handle:
            return handle.read()


class TestCase(unittest2.TestCase):
    """Provide a standard test environment for all suites of tests.

    Each set of tests starts in its own directory, and each test has
    its own unique prefix (testname) and config file path
    (conffile), so that the set of tests has a shared but separated
    environment, in which each test can run without collision.

    """

    testname = None
    conffile = None

    @classmethod
    def setUpClass(cls):
        """Set up tests in new, shared working directory and changes to it."""
        # pylint: disable=invalid-name
        # Save the current working directory to restore it later
        cls.oldcwd = os.getcwd()

        # Ensure the test root
        if not os.path.isdir(TESTDIR_BASE):
            os.mkdir(TESTDIR_BASE)

        # Create a new test directory and chdir to it
        cls.testdir = os.path.join(TESTDIR_BASE, cls.__name__)
        if os.path.isdir(cls.testdir):
            shutil.rmtree(cls.testdir)
        os.mkdir(cls.testdir)
        os.chdir(cls.testdir)

    @classmethod
    def tearDownClass(cls):
        """Return to the original working directory at the end of the test."""
        # pylint: disable=invalid-name
        os.chdir(cls.oldcwd)

    def setUp(self):
        """Provide function with reference to its own name and a conffile."""
        # pylint: disable=invalid-name
        self.testname = self.id().split('.')[-1]
        if self.conffile is None:
            self.conffile = '{0}.yaml'.format(self.testname)

    @staticmethod
    def _write_file(filename, filedata, mode=None):
        """Reusable method to create a file with the given contents."""
        if os.path.exists(filename):
            raise RuntimeError('{0} already exists'.format(filename))
        with open(filename, 'w') as testfh:
            wrapdata = textwrap.dedent(filedata).lstrip('\n')
            if sys.version_info.major == 2:
                testfh.write(wrapdata.encode('utf8'))
            else:
                testfh.write(wrapdata)
        if mode is not None:
            os.chmod(filename, mode)

    def _test_conf_good(self, confp, conftext):
        """Run the parser on the config text expecting success.

        Many test cases involve the successful parsing of a conffile.
        They all require the same sequence of steps: generating a
        config, configuring a parser to read that config, and then
        applying the parser to the config.  Once the config is
        successfully read into an object, various checks are performed
        to confirm the values.

        This function takes the confp parser and the config file
        text.  It writes the config text to a new config file, and
        calls the configured parser on the config file and returns the
        resulting conf object for subsequent checks.

        """
        self._write_file(self.conffile, conftext)
        conf = confp.parse_file(self.conffile)
        return conf

    def _test_conf_bad(self, confp, conftext, excrex=None):
        """Run the parser on the config text expecting failure.

        Many test cases involve confirming that a parser rejects a
        config file.  These often start by generating a config,
        configuring a parser to read that config, and then attempting
        to applying the parser to the config.  The test confirms that
        the parsing attempt raises an exception and often checks the
        exception text against a regular expression.

        This function takes the confp parser and the text of a
        config file.  It writes the config text to a new config file,
        and calls the configured parser on the config file and returns
        the resulting conf object for subsequent checks.

        """
        self._write_file(self.conffile, conftext)
        if excrex is None:
            with self.assertRaises(ParseError):
                confp.parse_file(self.conffile)
        else:
            with self.assertRaisesRegex(ParseError, excrex):
                confp.parse_file(self.conffile)

    def _rule_path_type_good(
            self, path_type, yamlvalue, testvalue=None, normalizer=None):
        """Test a rule path_type expecting success.

        Tests that a rule path_type successfully recognized a
        value type follow a pattern.  A config file is written that
        assigns the value to a field, a parser is configured with a
        rule that tests that the type of the field is a given type,
        the parser is run against the config file, and the resulting
        conf object is checked to see that the value is an instance of
        the given type, and that it has the correct value.  This
        function can be used to implement this pattern.

        Return the parsed config in case any additional testing is
        useful.

        If normalizer is given, it should be a function that
        transforms the field value parsed from the YAML before
        comparison with the test value.  This is used primarily to
        transform the timezone-aware datetime objects parsed from the
        YAML to the naive ones that are much easier to construct in
        older versions of python.

        """
        testvalue = yamlvalue if testvalue is None else testvalue
        confp = YamlConfigParser()
        confp.add_rule('field', path_type=path_type)
        conf = self._test_conf_good(confp, u'field: {0}'.format(yamlvalue))
        self.assertIsInstance(conf.field, path_type)
        if normalizer:
            self.assertEqual(normalizer(conf.field), testvalue)
        else:
            self.assertEqual(conf.field, testvalue)
        return conf

    def _rule_path_type_bad(self, path_type, yamlvalue, excrex):
        """Test a rule path_type expecting failure.

        A config file is written that assigns the value to a field, a
        parser is configured with a rule that tests the type of the
        field is a given type, an attempt is made to run the parser
        against the config file, and the test confirms that an
        exception is raised, and the exception message matches the
        given regex.  This function can me used to implement this
        pattern.

        """
        confp = YamlConfigParser()
        confp.add_rule('field', path_type=path_type)
        self._test_conf_bad(
            confp=confp,
            conftext=u'field: {0}'.format(yamlvalue),
            excrex=excrex)

    def _rule_test_good(
            self, testfunc, confvalue, quoted=False, testvalue=None):
        """Test a rule test against a value expecting success.

        A config file is written that assigns the value to a field, a
        parser is configured with the test function applied to that
        field, the parser is run against the config file, and the
        resulting conf object is checked to see that the value is
        correct.  This function can be used to implement this pattern
        in all such tests.

        Note that some test values must be quoted and escaped in the
        YAML.  In such cases, provide the expected value in testvalue
        and set quoted to True so that the value in the YAML will
        be escaped.

        In other cases, where python itself needs the value to be
        quoted to avoid evaluating it before writing it, you can
        specify a confvalue that will be written to the config and a
        separate testvalue that will be used in the final test.
        (This is used when a string version of a float must be
        written, unquoted to the YAML config, but we want to test it
        against the float value in the conf object.)

        Return the parsed config in case any additional testing is
        useful.

        """
        yamlvalue = u"'{0}'".format(confvalue) if quoted else confvalue
        testvalue = confvalue if testvalue is None else testvalue
        confp = YamlConfigParser()
        confp.add_rule('field', test=testfunc)
        conf = self._test_conf_good(confp, u'field: {0}'.format(yamlvalue))
        self.assertEqual(conf.field, testvalue)
        return conf

    def _rule_test_bad(self, testfunc, testvalue, excrex=None, quoted=False):
        """Test a rule test against a value expecting failure.

        A config file is written that assigns the value to a field, a
        parser is configured with the test function applied to that
        field, an attempt is made to run the parser against the config
        file, and the test confirms that a ParseError is raised,
        usually checking the value of the exception against a regular
        expression.

        """
        yamlvalue = u"'{0}'".format(testvalue) if quoted else testvalue
        confp = YamlConfigParser()
        confp.add_rule('field', test=testfunc)
        self._test_conf_bad(
            confp=confp,
            conftext=u'field: {0}'.format(yamlvalue),
            excrex=excrex)
