# -*- coding: utf-8 -*-

"""Test statements made in the documentation.

While several of these duplicate testing also performed in the
comprehensive yamlfig testing, they do so while duplicating or closely
approximating the code samples in the documentation.  As such, these
are intended to act a bit like coalmine canaries, giving us a heads up
if something we say in the documentation is or becomes untrue.

"""

# pylint: disable=too-many-lines, import-error, too-many-public-methods
# pylint: disable=line-too-long

from __future__ import absolute_import

# Standard modules
import functools
import os
import subprocess
import sys

from datetime import date, datetime

# Target package for testing
from yamlfig import YamlConfigParser, YamlConfig, YamlConfigList,\
    test, print_underscore_warning

# Shared testing basics - pytest enables the relative load
from testbase import CaptureIO, TestCase

# Globals
PYTHON_BIN = 'python'


class TestQuickstart(TestCase):
    """Test the Quick-start example from the README file."""

    @classmethod
    def setUpClass(cls):
        """Write shared script file and existing file referenced by docs."""
        super(TestQuickstart, cls).setUpClass()

        cls.scriptfile = 'quickstart_server.py'
        cls.sharedfile = 'quickstart_shared_file.txt'

        # Write the script
        cls._write_file(cls.scriptfile, """
        from __future__ import print_function
        import sys
        from yamlfig import YamlConfigParser, test

        # Construct a parser for the server config file
        confp = YamlConfigParser()
        confp.add_rule('name', path_type=str)
        confp.add_rule('description', optional=True)
        confp.add_rule('server.addr', path_type=str, default='127.0.0.1', test=test.is_ipv4_address)
        confp.add_rule('server.port', path_type=int, test=test.is_interval(1, 65535, include_upper=True))
        confp.add_rule('file_path', path_type=str, test=test.is_file_path('exists', 'isfile'))
        confp.add_rule('users', path_type=list)
        confp.add_rule('users.*', test=test.is_regex('^[a-z][a-z0-9]*$'))

        # Parse the config file
        conf = confp.parse_file(sys.argv[1])

        # Retrieve values from the conf object
        print('conf.name = {0}'.format(repr(conf.name)))
        print('conf.description = {0}'.format(repr(conf.description)))
        print('conf.server.addr = {0}'.format(repr(conf.server.addr)))
        print('conf.server.port = {0}'.format(repr(conf.server.port)))
        print('conf.file_path = {0}'.format(repr(conf.file_path)))
        for idx in conf.users:
          print('conf.users[{0}] = {1}'.format(idx, repr(conf.users[idx])))
        """)

        # Create the shared file
        cls._write_file(
            cls.sharedfile, 'Hello users!  Here is stuff to share...')

    def test_quickstart_server_good(self):
        """Write simple server config file and test.

        We construct a simple but complete parser for the config file
        of an application that runs a simple server to listen on an IP
        address and port, allow access from explicitly listed user
        accounts, and serve up the contents of a file.

        This test should verbatim match the scenario in Quick-Start
        Example in README.md.

        """
        # Configure test variables
        conffile = 'quickstart_server.yaml'

        # Set up the config file
        self._write_file(conffile, """
        name: Simple Single-File Server
        server:
          port: 81
        file_path: '{0}'
        users:
        - alice
        - bob
        - carol
        """.format(self.sharedfile))

        # Invoke the script and capture the output
        with CaptureIO(self.testname) as capio:
            retval = subprocess.call(
                [PYTHON_BIN, self.scriptfile, conffile],
                stdout=capio.stdout,
                stderr=capio.stderr)
        output = capio.get_stdout().splitlines()
        stderr = capio.get_stderr()

        # Test that the output matches the expected values
        self.assertEqual(retval, 0)
        self.assertEqual(output[0], "conf.name = 'Simple Single-File Server'")
        self.assertEqual(output[1], "conf.description = None")
        self.assertEqual(output[2], "conf.server.addr = '127.0.0.1'")
        self.assertEqual(output[3], "conf.server.port = 81")
        self.assertEqual(
            output[4], "conf.file_path = '{0}'".format(self.sharedfile))
        self.assertEqual(output[5], "conf.users[0] = 'alice'")
        self.assertEqual(output[6], "conf.users[1] = 'bob'")
        self.assertEqual(output[7], "conf.users[2] = 'carol'")
        self.assertEqual(stderr, '')

    def test_quickstart_server_bad_name(self):
        """Missing name field should raise error."""
        # Configure test variables
        conffile = self.conffile

        # Set up the config file
        self._write_file(conffile, """
        server:
          port: 81
        file_path: '{0}'
        users:
        - alice
        - bob
        - carol
        """.format(self.sharedfile))

        # Invoke the script and capture the output
        with CaptureIO(self.testname) as capio:
            retval = subprocess.call(
                [PYTHON_BIN, self.scriptfile, conffile],
                stdout=capio.stdout,
                stderr=capio.stderr)
        stderr = capio.get_stderr()

        # Parse the error
        self.assertNotEqual(retval, 0)
        self.assertRegex(stderr, '"name" is missing')

    def test_quickstart_server_bad_extra_field(self):
        """Unexpected server.address field should raise error."""
        # Configure test variables
        conffile = self.conffile
        sharedfile = '{0}_shared_file.txt'.format(self.testname)

        # Set up the config file
        self._write_file(conffile, """
        name: Simple Single-File Server
        server:
          the_ip_address: 0.0.0.0
          port: 81
        file_path: '{0}'
        users:
        - alice
        - bob
        - carol
        """.format(sharedfile))

        # Invoke the script and capture the output
        with CaptureIO(self.testname) as capio:
            retval = subprocess.call(
                [PYTHON_BIN, self.scriptfile, conffile],
                stdout=capio.stdout,
                stderr=capio.stderr)
        stderr = capio.get_stderr()

        # Parse the error
        self.assertNotEqual(retval, 0)
        self.assertRegex(stderr, '"server.the_ip_address" unexpected by parser')

    def test_quickstart_server_bad_port(self):
        """Type error on server.port should raise error."""
        # Configure test variables
        conffile = self.conffile
        sharedfile = '{0}_shared_file.txt'.format(self.testname)

        # Set up the config file
        self._write_file(conffile, """
        name: Simple Single-File Server
        server:
          port: eighty-one
        file_path: '{0}'
        users:
        - alice
        - bob
        - carol
        """.format(sharedfile))

        # Invoke the script and capture the output
        with CaptureIO(self.testname) as capio:
            retval = subprocess.call(
                [PYTHON_BIN, self.scriptfile, conffile],
                stdout=capio.stdout,
                stderr=capio.stderr)
        stderr = capio.get_stderr()

        # Parse the error
        self.assertNotEqual(retval, 0)
        self.assertRegex(stderr, '"server.port" has type str not type int')

    def test_quickstart_server_bad_addr(self):
        """Invalid IPv4 in server.addr field should raise error."""
        # Configure test variables
        conffile = self.conffile
        sharedfile = '{0}_shared_file.txt'.format(self.testname)

        # Set up the config file
        self._write_file(conffile, """
        name: Simple Single-File Server
        server:
          addr: 452.34.256.193
          port: 81
        file_path: '{0}'
        users:
        - alice
        - bob
        - carol
        """.format(sharedfile))

        # Invoke the script and capture the output
        with CaptureIO(self.testname) as capio:
            retval = subprocess.call(
                [PYTHON_BIN, self.scriptfile, conffile],
                stdout=capio.stdout,
                stderr=capio.stderr)
        stderr = capio.get_stderr()

        # Parse the error
        self.assertNotEqual(retval, 0)
        self.assertRegex(
            stderr,
            '"server.addr" failed test: 1st octet of "452.34.256.193" ' +
            'exceeds 255')

    def test_quickstart_server_bad_file_path(self):
        """Directory rather than file in file_path value should raise error."""
        # Configure test variables
        conffile = self.conffile
        somedir = '{0}_somedir'.format(self.testname)

        # Set up the config file
        self._write_file(conffile, """
        name: Simple Single-File Server
        server:
          port: 81
        file_path: '{0}'
        users:
        - alice
        - bob
        - carol
        """.format(somedir))

        # Create the referenced directory
        os.mkdir(somedir)

        # Invoke the script and capture the output
        with CaptureIO(self.testname) as capio:
            retval = subprocess.call(
                [PYTHON_BIN, self.scriptfile, conffile],
                stdout=capio.stdout,
                stderr=capio.stderr)
        stderr = capio.get_stderr()

        # Parse the error
        self.assertNotEqual(retval, 0)
        self.assertRegex(
            stderr,
            '"file_path" failed test: "{0}" is not a file'.format(somedir))

    def test_quickstart_server_bad_user(self):
        """User not matching the regex should raise error."""
        # Configure test variables
        conffile = self.conffile
        sharedfile = '{0}_shared_file.txt'.format(self.testname)

        # Set up the config file
        self._write_file(conffile, """
        name: Simple Single-File Server
        server:
          port: 81
        file_path: '{0}'
        users:
        - alice
        - bob
        - Carol C.
        """.format(sharedfile))

        # Create the referenced shared file
        self._write_file(sharedfile, 'Hello users!  Here is stuff to share...')

        # Invoke the script and capture the output
        with CaptureIO(self.testname) as capio:
            retval = subprocess.call(
                [PYTHON_BIN, self.scriptfile, conffile],
                stdout=capio.stdout,
                stderr=capio.stderr)
        stderr = capio.get_stderr()

        # Parse the error
        self.assertNotEqual(retval, 0)
        self.assertRegex(
            stderr,
            '"users.2" failed test: ' +
            r'"Carol C." does not match /\^\[a-z\]\[a-z0-9\]\*\$/')


class TestBasicUsage(TestCase):
    """Test the Basic Usage examples from the README file."""

    @classmethod
    def setUpClass(cls):
        """Write the three-fields script file from the README."""
        super(TestBasicUsage, cls).setUpClass()

        cls.scriptfile = 'basic_usage.py'
        cls._write_file(cls.scriptfile, '''
        ##### Initial Setup #####
        from __future__ import print_function

        def special_function(param):
          print('special_function\t{0}'.format(param))

        def regular_function(param):
          print('regular_function\t{0}'.format(param))

        ##### Begin Example Code #####
        import sys

        from yamlfig import YamlConfigParser

        # 1. Instantiate a YamlConfigParser object (confp)
        confp = YamlConfigParser()

        # 2. Configure the parser by adding rules for each field
        confp.add_rule('loop_count')
        confp.add_rule('do_special_function')
        confp.add_rule('function_parameter')

        # 3. Invoke the parser on a config file (provided as an argument)
        conf = confp.parse_file(sys.argv[1])

        # 4. Use the YamlConfig object in subsequent code
        for loop_index in range(conf.loop_count):
          if conf.do_special_function:
            special_function(conf.function_parameter)
          else:
            regular_function(conf.function_parameter)
        ''')

    def _validate_script_output(self, text, funcname, funcparam, funccount):
        # Parse function invocation info from text and compare with expected
        invokedcount = 0
        for line in text.splitlines():
            invokedname, invokedparam = line.split('\t')
            self.assertEqual(invokedname, funcname)
            self.assertEqual(invokedparam, funcparam)
            invokedcount += 1
        self.assertEqual(invokedcount, funccount)

    def test_basic_usage_config_1(self):
        """Test typical yamlfig usage pattern."""
        conffile = 'basic_config_1.yaml'

        # Write the config file
        self._write_file(conffile, '''
        loop_count: 7
        do_special_function: yes
        function_parameter: "a meerkat"
        ''')

        # Invoke the script on the config file and capture the output
        with CaptureIO(self.testname) as capio:
            retval = subprocess.call(
                [PYTHON_BIN, self.scriptfile, conffile],
                stdout=capio.stdout,
                stderr=capio.stderr)

        # Validate the expected behavior
        self.assertEqual(retval, 0)
        self._validate_script_output(
            capio.get_stdout(), 'special_function', 'a meerkat', 7)
        self.assertEqual(capio.get_stderr(), '')

    def test_basic_usage_config_2(self):
        """Test typical yamlfig usage pattern."""
        conffile = 'basic_config_2.yaml'

        # Write the config file
        self._write_file(conffile, '''
        loop_count: 3
        do_special_function: no
        function_parameter: a pony
        ''')

        # Invoke the script on the config file and capture the output
        with CaptureIO(self.testname) as capio:
            retval = subprocess.call(
                [PYTHON_BIN, self.scriptfile, conffile],
                stdout=capio.stdout,
                stderr=capio.stderr)

        # Validate the expected behavior
        self.assertEqual(retval, 0)
        self._validate_script_output(
            capio.get_stdout(), 'regular_function', 'a pony', 3)
        self.assertEqual(capio.get_stderr(), '')

    def test_basic_usage_config_bad(self):
        """Test typical yamlfig usage pattern."""
        conffile = 'basic_config_bad.yaml'

        # Write the config file
        self._write_file(conffile, '''
        loop_count: 42
        function_parameter: 'a unicord'
        ''')

        # Invoke the script on the config file and capture the output
        with CaptureIO(self.testname) as capio:
            retval = subprocess.call(
                [PYTHON_BIN, self.scriptfile, conffile],
                stdout=capio.stdout,
                stderr=capio.stderr)

        # Validate the expected behavior
        self.assertEqual(retval, 1)
        self.assertEqual(capio.get_stdout(), '')
        self.assertRegex(
            capio.get_stderr(),
            'basic_config_bad.yaml: "do_special_function" is missing')


class TestFieldsPathsStructure(TestCase):
    """Check statements in "Fields, Paths, and Structures" in the README."""

    def test_that_a_field_exists_good(self):
        """Test that a field exists."""
        confp = YamlConfigParser()
        confp.add_rule('dirname')
        conf = self._test_conf_good(confp, '''
        dirname: /var/share/SomeApp/SharedDir
        ''')
        self.assertEqual(conf.dirname, '/var/share/SomeApp/SharedDir')

    def test_that_a_field_exists_bad(self):
        """Test that a field exists."""
        confp = YamlConfigParser()
        confp.add_rule('dirname')
        self._test_conf_bad(
            confp=confp,
            conftext='{}',
            excrex='"dirname" is missing')

    def test_that_a_path_exists(self):
        """Test that a path exists."""
        confp = YamlConfigParser()
        confp.add_rule('server.storage.dirname')
        conf = self._test_conf_good(confp, '''
        server:
          storage:
            dirname: /var/share/SomeApp/SharedDir
        ''')
        self.assertEqual(
            conf.server.storage.dirname, '/var/share/SomeApp/SharedDir')

    def test_that_a_block_has_a_specific_substructure(self):
        """Test that a block has a specific substructure."""
        confp = YamlConfigParser()
        confp.add_rule('server.storage.dirname')
        confp.add_rule('server.storage.maxsize')
        confp.add_rule('server.storage.umask')
        conf = self._test_conf_good(confp, '''
        server:
          storage:
            dirname: /var/share/SomeApp/SharedDir
            maxsize: 10GB
            umask: 0644
        ''')
        self.assertEqual(
            conf.server.storage.dirname, '/var/share/SomeApp/SharedDir')
        self.assertEqual(conf.server.storage.maxsize, '10GB')
        self.assertEqual(conf.server.storage.umask, 0o644)

    def test_that_a_block_contains_a_mapping_using_wildcards_good_1(self):
        """Test that a block contains a mapping using wildcards."""
        confp = YamlConfigParser()
        confp.add_rule('server.upload_paths.*')
        conf = self._test_conf_good(confp, '''
        server:
          upload_paths:
            alice:   /home/alice/uploads
            bob:     /home/bob/public
        ''')
        self.assertSetEqual(set(conf.server.upload_paths), {'alice', 'bob'})
        self.assertEqual(
            conf.server.upload_paths.alice, '/home/alice/uploads')
        self.assertEqual(
            conf.server.upload_paths.bob, '/home/bob/public')

    def test_that_a_block_contains_a_mapping_using_wildcards_good_2(self):
        """Test that a block contains a mapping using wildcards."""
        confp = YamlConfigParser()
        confp.add_rule('server.upload_paths.*')
        conf = self._test_conf_good(confp, '''
        server:
          upload_paths:
            alice:   /home/alice/uploads
            bob:     /home/bob/public
            carol:   /home/carol/tmp
        ''')
        self.assertSetEqual(
            set(conf.server.upload_paths), {'alice', 'bob', 'carol'})
        self.assertEqual(
            conf.server.upload_paths.alice, '/home/alice/uploads')
        self.assertEqual(
            conf.server.upload_paths.bob, '/home/bob/public')
        self.assertEqual(
            conf.server.upload_paths.carol, '/home/carol/tmp')

    def test_that_a_block_contains_a_mapping_using_wildcards_bad_1(self):
        """Test that a block contains a mapping using wildcards."""
        confp = YamlConfigParser()
        confp.add_rule('server.upload_paths.*')
        self._test_conf_bad(
            confp=confp,
            conftext='''
            server:
              upload_paths: {}
            ''',
            excrex='"server.upload_paths" must contain at least one field')

    def test_that_a_block_contains_a_mapping_using_wildcards_bad_2(self):
        """Test that a block contains a mapping using wildcards."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError, 'cannot use a partial wildcard'):
            confp.add_rule('server.upload_paths.user-*')

    def test_that_each_block_in_a_mapping_has_matching_good(self):
        """Test that each block in a mapping has matching substructure."""
        confp = YamlConfigParser()
        confp.add_rule('projects.*.webpath')
        confp.add_rule('projects.*.dbpath')
        confp.add_rule('projects.*.dbtype')
        conf = self._test_conf_good(confp, '''
        projects:
          ProjectX:
            webpath: /home/alice/projx/html
            dbpath:  /home/alice/projx/project.db
            dbtype: sqlite
          meerkat_works:
            webpath: /home/bob/public/meerkat/www
            dbpath:  mongodb://192.168.1.200:27017
            dbtype: mongodb
        ''')
        self.assertSetEqual(set(conf.projects), {'ProjectX', 'meerkat_works'})
        self.assertEqual(conf.projects.ProjectX.dbtype, 'sqlite')
        self.assertEqual(conf.projects.meerkat_works.dbtype, 'mongodb')

    def test_that_each_block_in_a_mapping_has_matching_bad_1(self):
        """Test that each block in a mapping has matching substructure."""
        confp = YamlConfigParser()
        confp.add_rule('projects.*.webpath')
        confp.add_rule('projects.*.dbpath')
        confp.add_rule('projects.*.dbtype')
        self._test_conf_bad(
            confp=confp,
            conftext='''
            projects:
              ProjectX:
                webpath: /home/alice/projx/html
                dbpath:  /home/alice/projx/project.db
                dbtype: sqlite
              meerkat_works:
                webpath: /home/bob/public/meerkat/www
                dbtype: mongodb
            ''',
            excrex='"projects.meerkat_works.dbpath" is missing')

    def test_that_each_block_in_a_mapping_has_matching_bad_2(self):
        """Test that each block in a mapping has matching substructure."""
        confp = YamlConfigParser()
        confp.add_rule('projects.*.webpath')
        confp.add_rule('projects.*.dbpath')
        confp.add_rule('projects.*.dbtype')
        self._test_conf_bad(
            confp=confp,
            conftext='''
            projects:
              ProjectX:
                webpath: /home/alice/projx/html
                dbpath:  /home/alice/projx/project.db
                dbtype: sqlite
                webtype: IM-AN-EXTRA-VALUE
              meerkat_works:
                webpath: /home/bob/public/meerkat/www
                dbpath:  /home/alice/projx/project.db
                dbtype: mongodb
            ''',
            excrex='"projects.ProjectX.webtype" unexpected by parser')

    def test_that_a_block_contains_a_list_using_wildcards_good_1(self):
        """Test that a block contains a list using wildcards."""
        confp = YamlConfigParser()
        confp.add_rule('users.*')
        conf = self._test_conf_good(confp, '''
        users:
        - alice
        - bob
        - carol
        ''')
        self.assertListEqual(list(conf.users), ['0', '1', '2'])
        self.assertListEqual(
            [conf.users[idx] for idx in conf.users], ['alice', 'bob', 'carol'])

    def test_that_a_block_contains_a_list_using_wildcards_good_2(self):
        """Test that a block contains a list using wildcards."""
        confp = YamlConfigParser()
        confp.add_rule('users.*')
        conf = self._test_conf_good(confp, '''
        users:
          alice:  Alice A.
          bob:    Bob B.
          carol:  Carol C.
        ''')
        self.assertSetEqual(set(conf.users), {'alice', 'bob', 'carol'})
        self.assertSetEqual(
            {conf.users[user] for user in conf.users},
            {'Alice A.', 'Bob B.', 'Carol C.'})

    def test_that_a_list_has_exactly_n_elements_good_list(self):
        """Test that a list has exactly n elements."""
        confp = YamlConfigParser()
        confp.add_rule('network.route.0')
        confp.add_rule('network.route.1')
        conf = self._test_conf_good(confp, '''
        network:
          route:
          - 192.0.2.1
          - 198.51.100.1
        ''')
        self.assertListEqual(list(conf.network.route), ['0', '1'])
        self.assertEqual(conf.network.route[0], '192.0.2.1')
        self.assertEqual(conf.network.route[1], '198.51.100.1')

    def test_that_a_list_has_exactly_n_elements_good_map(self):
        """Test that a list has exactly n elements."""
        confp = YamlConfigParser()
        confp.add_rule('network.route.0')
        confp.add_rule('network.route.1')
        conf = self._test_conf_good(confp, '''
        network:
          route:
            '0': 192.0.2.1
            '1': 198.51.100.1
        ''')
        self.assertListEqual(list(conf.network.route), ['0', '1'])
        self.assertEqual(conf.network.route['0'], '192.0.2.1')
        self.assertEqual(conf.network.route['1'], '198.51.100.1')


class TestHandlingParsedObjects(TestCase):
    """Check statements in "Handling Parsed Objects" in the README."""

    @classmethod
    def setUpClass(cls):
        """Construct parser, write config file, parse and store conf."""
        super(TestHandlingParsedObjects, cls).setUpClass()
        cls.conffile = 'handling_parsed_objects.yaml'
        confp = YamlConfigParser()
        confp.add_rule('dirname')
        confp.add_rule('server.projects.*.webpath')
        confp.add_rule('server.projects.*.dbpath')
        confp.add_rule('server.projects.*.dbtype')
        confp.add_rule('users.*')
        cls._write_file(cls.conffile, '''
        dirname: /var/share/SomeApp/SharedDir
        server:
          projects:
            ProjectX:
              webpath: /home/alice/projx/html
              dbpath:  /home/alice/projx/project.db
              dbtype: sqlite
            meerkat_works:
              webpath: /home/bob/public/meerkat/www
              dbpath:  mongodb://192.168.1.200:27017
              dbtype: mongodb
        users:
        - alice
        - bob
        - carol
        - dave
        ''')
        cls.conf = confp.parse_file(cls.conffile)

    def test_fields_and_paths_can_be_accessed_as_attributes(self):
        """Access fields and paths as attributes."""
        conf = self.conf

        self.assertEqual(conf.dirname, '/var/share/SomeApp/SharedDir')

        self.assertRegex(repr(conf.server), '<.*YamlConfig object at 0x.*>')
        self.assertRegex(repr(conf.users), '<.*YamlConfigList object at 0x.*>')

        self.assertEqual(
            conf.server.projects.ProjectX.webpath,
            '/home/alice/projx/html')
        self.assertEqual(
            conf.server.projects.ProjectX.dbpath,
            '/home/alice/projx/project.db')
        self.assertEqual(conf.server.projects.ProjectX.dbtype, 'sqlite')

        self.assertEqual(conf.server.projects.meerkat_works.dbtype, 'mongodb')

    def test_fields_and_paths_can_be_accessed_via_index_lookups(self):
        """Access fields and paths via index lookups."""
        conf = self.conf

        self.assertEqual(conf.server.projects['ProjectX'].dbtype, 'sqlite')

        proj = 'ProjectX'
        self.assertEqual(conf.server.projects[proj].dbtype, 'sqlite')

        self.assertEqual(
            conf['server']['projects']['ProjectX']['dbtype'], 'sqlite')

        path = ['server', 'projects', 'ProjectX', 'dbtype']
        self.assertEqual(
            functools.reduce(lambda d, idx: d[idx], path, conf), 'sqlite')

    def test_list_values_can_be_accessed_via_index_lookups(self):
        """Access list values via index lookups."""
        conf = self.conf

        self.assertEqual(conf.users[0], 'alice')
        self.assertEqual(conf.users[1], 'bob')
        self.assertEqual(conf.users[2], 'carol')
        self.assertEqual(conf.users[3], 'dave')

        self.assertEqual(conf.users[-1], 'dave')
        self.assertEqual(conf.users[-2], 'carol')

        self.assertEqual(conf.users["1"], 'bob')
        self.assertEqual(conf.users['-2'], 'carol')

    def test_length_checks_can_be_used_to_determine_number_of_fields(self):
        """Use length checks to determine the number of fields."""
        conf = self.conf

        self.assertEqual(len(conf), 3)
        self.assertEqual(len(conf.server), 1)
        self.assertEqual(len(conf.server.projects), 2)
        self.assertEqual(len(conf.server.projects.ProjectX), 3)
        self.assertEqual(len(conf.server.projects.meerkat_works), 3)
        self.assertEqual(len(conf.users), 4)

    def test_iterators_return_field_names_for_yamlconfig_objects(self):
        """Check YamlConfig iterators return field names."""
        conf = self.conf

        self.assertListEqual(list(conf), ['dirname', 'server', 'users'])
        self.assertListEqual(list(conf.server), ['projects'])
        self.assertSetEqual(
            set(conf.server.projects), {'ProjectX', 'meerkat_works'})
        self.assertListEqual(
            list(conf.server.projects.ProjectX),
            ['webpath', 'dbpath', 'dbtype'])
        self.assertListEqual(
            list(conf.server.projects.meerkat_works),
            ['webpath', 'dbpath', 'dbtype'])

    def test_iterators_return_list_indexes_for_yamlconfiglist_objects(self):
        """Check YamlConfigList iterators return list indexes."""
        conf = self.conf

        self.assertListEqual(list(conf.users), ['0', '1', '2', '3'])
        self.assertListEqual(
            [conf.users[idx] for idx in conf.users],
            ['alice', 'bob', 'carol', 'dave'])


class TestOptionalDefaultNoFollowRules(TestCase):
    """Check statements in "Optional, Default, and No-Follow Rules"."""

    def test_a_field_flagged_optional_can_be_omitted_good_1(self):
        """A field flagged as optional can be omitted."""
        confp = YamlConfigParser()
        confp.add_rule('name')
        confp.add_rule('description', optional=True)
        conf = self._test_conf_good(confp, 'name: Simple Single-File Server')
        self.assertEqual(conf.name, 'Simple Single-File Server')
        self.assertIsNone(conf.description)

    def test_a_field_flagged_optional_can_be_omitted_good_2(self):
        """A field flagged as optional can be omitted."""
        confp = YamlConfigParser()
        confp.add_rule('name')
        confp.add_rule('description', optional=True)
        conf = self._test_conf_good(confp, '''
        name: Simple Single-File Server
        description: null
        ''')
        self.assertEqual(conf.name, 'Simple Single-File Server')
        self.assertIsNone(conf.description)

    def test_optional_fields_can_have_required_substructure_good_1(self):
        """Optional fields can have required substructure."""
        confp = YamlConfigParser()
        confp.add_rule('server.addr')
        confp.add_rule('server.port')
        confp.add_rule('server.ssl', optional=True)
        confp.add_rule('server.ssl.key')
        confp.add_rule('server.ssl.cert')
        confp.add_rule('server.ssl.chain')
        conf = self._test_conf_good(confp, '''
        server:
          addr: 127.0.0.1
          port: 81
        ''')
        self.assertEqual(conf.server.addr, '127.0.0.1')
        self.assertEqual(conf.server.port, 81)
        self.assertIsNone(conf.server.ssl)

    def test_optional_fields_can_have_required_substructure_good_2(self):
        """Optional fields can have required substructure."""
        confp = YamlConfigParser()
        confp.add_rule('server.addr')
        confp.add_rule('server.port')
        confp.add_rule('server.ssl', optional=True)
        confp.add_rule('server.ssl.key')
        confp.add_rule('server.ssl.cert')
        confp.add_rule('server.ssl.chain')
        conf = self._test_conf_good(confp, '''
        server:
          addr: 127.0.0.1
          port: 81
          ssl:
            key: /etc/ssl/privkey.pem
            cert: /etc/ssl/cert.pem
            chain: /etc/ssl/full_chain.pem
        ''')
        self.assertEqual(conf.server.addr, '127.0.0.1')
        self.assertEqual(conf.server.port, 81)
        self.assertRegex(repr(conf.server.ssl), '<.*YamlConfig object at 0x.*>')
        self.assertEqual(conf.server.ssl.key, '/etc/ssl/privkey.pem')
        self.assertEqual(conf.server.ssl.cert, '/etc/ssl/cert.pem')
        self.assertEqual(conf.server.ssl.chain, '/etc/ssl/full_chain.pem')

    def test_optional_fields_can_have_required_substructure_bad(self):
        """Optional fields can have required substructure."""
        confp = YamlConfigParser()
        confp.add_rule('server.addr')
        confp.add_rule('server.port')
        confp.add_rule('server.ssl', optional=True)
        confp.add_rule('server.ssl.key')
        confp.add_rule('server.ssl.cert')
        confp.add_rule('server.ssl.chain')
        self._test_conf_bad(
            confp=confp,
            conftext='''
            server:
              addr: 127.0.0.1
              port: 81
              ssl:
                key: /etc/ssl/privkey.pem
                # cert: /etc/ssl/cert.pem
                chain: /etc/ssl/full_chain.pem
            ''',
            excrex='"server.ssl.cert" is missing')

    def test_a_default_field_will_take_a_default_value_if_omitted_good_1(self):
        """A default field will take a default value if omitted."""
        confp = YamlConfigParser()
        confp.add_rule('server.addr', default='127.0.0.1')
        confp.add_rule('server.port')
        conf = self._test_conf_good(confp, '''
        server:
          port: 81
        ''')
        self.assertEqual(conf.server.addr, '127.0.0.1')
        self.assertEqual(conf.server.port, 81)

    def test_a_default_field_will_take_a_default_value_if_omitted_good_2(self):
        """A default field will take a default value if omitted."""
        confp = YamlConfigParser()
        confp.add_rule('server.addr', default='127.0.0.1')
        confp.add_rule('server.port')
        conf = self._test_conf_good(confp, '''
        server:
          addr: 0.0.0.0
          port: 81
        ''')
        self.assertEqual(conf.server.addr, '0.0.0.0')
        self.assertEqual(conf.server.port, 81)

    def test_default_substructure_must_still_undergo_validation_bad(self):
        """Default substructure must still undergo validation."""
        confp = YamlConfigParser()
        confp.add_rule('server', default={'addr': '127.0.0.1', 'port': 81})
        self._test_conf_bad(
            confp=confp,
            conftext='{}',
            excrex='"server.(addr|port)" unexpected by parser')

    def test_default_substructure_must_still_undergo_validation_good(self):
        """Default substructure must still undergo validation."""
        confp = YamlConfigParser()
        confp.add_rule('server', default={'addr': '127.0.0.1', 'port': 81})
        confp.add_rule('server.addr')
        confp.add_rule('server.port')
        conf = self._test_conf_good(confp, '{}')
        self.assertEqual(conf.server.addr, '127.0.0.1')
        self.assertEqual(conf.server.port, 81)

    def test_fields_cannot_both_be_optional_and_take_a_default(self):
        """Field cannot both be optional and take a default."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError, '"field" cannot be optional and have a default'):
            confp.add_rule('field', optional=True, default='default_value')

    def test_default_path_can_have_optional_subpaths_vice_versa_1(self):
        """A default path can have optional subpaths and vice versa.

        This is an optional within default case.

        """
        confp = YamlConfigParser()
        confp.add_rule('server', default={'addr': '127.0.0.1', 'port': 81})
        confp.add_rule('server.addr')
        confp.add_rule('server.port')
        confp.add_rule('server.ssl', optional=True)
        confp.add_rule('server.ssl.key')
        confp.add_rule('server.ssl.cert')
        confp.add_rule('server.ssl.chain')
        conf = self._test_conf_good(confp, 'server:')
        self.assertRegex(repr(conf.server), '<.*YamlConfig object at 0x.*>')
        self.assertEqual(conf.server.addr, '127.0.0.1')
        self.assertEqual(conf.server.port, 81)
        self.assertIsNone(conf.server.ssl)

    def test_default_path_can_have_optional_subpaths_vice_versa_2(self):
        """A default path can have optional subpaths and vice versa.

        This is a default within optional case.

        """
        confp = YamlConfigParser()
        confp.add_rule('server', optional=True)
        confp.add_rule('server.addr')
        confp.add_rule('server.port')
        confp.add_rule('server.ssl', default={
            'key': '/etc/ssl/privkey.pem',
            'cert': '/etc/ssl/cert.pem',
            'chain': '/etc/ssl/chain.pem'
        })
        confp.add_rule('server.ssl.key')
        confp.add_rule('server.ssl.cert')
        confp.add_rule('server.ssl.chain')
        conf = self._test_conf_good(confp, 'server:')
        self.assertIsNone(conf.server)

    def test_default_path_can_have_optional_subpaths_vice_versa_3(self):
        """A default path can have optional subpaths and vice versa.

        This is a default within optional case.

        """
        confp = YamlConfigParser()
        confp.add_rule('server', optional=True)
        confp.add_rule('server.addr')
        confp.add_rule('server.port')
        confp.add_rule('server.ssl', default={
            'key': '/etc/ssl/privkey.pem',
            'cert': '/etc/ssl/cert.pem',
            'chain': '/etc/ssl/chain.pem'
        })
        confp.add_rule('server.ssl.key')
        confp.add_rule('server.ssl.cert')
        confp.add_rule('server.ssl.chain')
        conf = self._test_conf_good(confp, '''
        server:
          addr: 127.0.0.1
          port: 81
        ''')
        self.assertEqual(conf.server.ssl.key, '/etc/ssl/privkey.pem')
        self.assertEqual(conf.server.ssl.cert, '/etc/ssl/cert.pem')
        self.assertEqual(conf.server.ssl.chain, '/etc/ssl/chain.pem')

    def test_default_path_can_have_optional_subpaths_vice_versa_4(self):
        """A default path can have optional subpaths and vice versa.

        This is a default within default case.

        """
        confp = YamlConfigParser()
        confp.add_rule('server', default={'addr': '127.0.0.1', 'port': 81})
        confp.add_rule('server.addr')
        confp.add_rule('server.port')
        confp.add_rule('server.ssl', default={
            'key': '/etc/ssl/privkey.pem',
            'cert': '/etc/ssl/cert.pem',
            'chain': '/etc/ssl/chain.pem'
        })
        confp.add_rule('server.ssl.key')
        confp.add_rule('server.ssl.cert')
        confp.add_rule('server.ssl.chain')
        conf = self._test_conf_good(confp, '{}')
        self.assertEqual(conf.server.addr, '127.0.0.1')
        self.assertEqual(conf.server.port, 81)
        self.assertEqual(conf.server.ssl.key, '/etc/ssl/privkey.pem')
        self.assertEqual(conf.server.ssl.cert, '/etc/ssl/cert.pem')
        self.assertEqual(conf.server.ssl.chain, '/etc/ssl/chain.pem')

    def test_default_path_can_have_optional_subpaths_vice_versa_5(self):
        """A default path can have optional subpaths and vice versa.

        This is an optional within optional case.

        """
        confp = YamlConfigParser()
        confp.add_rule('server', optional=True)
        confp.add_rule('server.addr')
        confp.add_rule('server.port')
        confp.add_rule('server.ssl', optional=True)
        confp.add_rule('server.ssl.key')
        confp.add_rule('server.ssl.cert')
        confp.add_rule('server.ssl.chain')
        conf = self._test_conf_good(confp, '{}')
        self.assertIsNone(conf.server)

    def test_default_path_can_have_optional_subpaths_vice_versa_6(self):
        """A default path can have optional subpaths and vice versa.

        This is an optional within optional case.

        """
        confp = YamlConfigParser()
        confp.add_rule('server', optional=True)
        confp.add_rule('server.addr')
        confp.add_rule('server.port')
        confp.add_rule('server.ssl', optional=True)
        confp.add_rule('server.ssl.key')
        confp.add_rule('server.ssl.cert')
        confp.add_rule('server.ssl.chain')
        conf = self._test_conf_good(confp, '''
        server:
          addr: 127.0.0.1
          port: 81
        ''')
        self.assertIsNone(conf.server.ssl)

    def test_default_block_and_optional_wildcard_recognize_zero_or_more_1(self):
        """Implement zero-or-more using default block and optional wildcards."""
        confp = YamlConfigParser()
        confp.add_rule('server.upload_paths', default={})
        confp.add_rule('server.upload_paths.*', optional=True)
        conf = self._test_conf_good(confp, 'server: {}')
        self.assertRegex(
            repr(conf.server.upload_paths), '<.*YamlConfig object at 0x.*>')
        self.assertEqual(len(conf.server.upload_paths), 0)

    def test_default_block_and_optional_wildcard_recognize_zero_or_more_2(self):
        """Implement zero-or-more using default block and optional wildcards."""
        confp = YamlConfigParser()
        confp.add_rule('server.upload_paths', default={})
        confp.add_rule('server.upload_paths.*', optional=True)
        conf = self._test_conf_good(confp, '''
        server:
          upload_paths:
            alice:   /home/alice/uploads
            bob:     /home/bob/public
        ''')
        self.assertRegex(
            repr(conf.server.upload_paths), '<.*YamlConfig object at 0x.*>')
        self.assertEqual(len(conf.server.upload_paths), 2)
        self.assertSetEqual(set(conf.server.upload_paths), {'alice', 'bob'})

    def test_path_marked_nofollow_can_have_arbitrary_substructure_1(self):
        """A path marked no-follow can have any and arbitrary substructure."""
        confp = YamlConfigParser()
        confp.add_rule('mongodburl')
        confp.add_rule('collection')
        confp.add_rule('filterquery', nofollow=True)
        conf = self._test_conf_good(confp, '''
        mongodburl: mongodb://192.168.1.200:27017/
        collection: projects
        filterquery: { 'is_private': { '$ne': true } }
        ''')
        self.assertEqual(conf.mongodburl, 'mongodb://192.168.1.200:27017/')
        self.assertEqual(conf.collection, 'projects')
        self.assertDictEqual(conf.filterquery, {'is_private': {'$ne': True}})
        self.assertEqual(
            repr(conf.filterquery), "{'is_private': {'$ne': True}}")

    def test_path_marked_nofollow_can_have_arbitrary_substructure_2(self):
        """A path marked no-follow can have any and arbitrary substructure."""
        confp = YamlConfigParser()
        confp.add_rule('mongodburl')
        confp.add_rule('collection')
        confp.add_rule('filterquery', nofollow=True)
        conf = self._test_conf_good(confp, '''
        mongodburl: mongodb://192.168.1.200:27017/
        collection: projects
        filterquery:
          is_private:
            "$ne": true
        ''')
        self.assertEqual(conf.mongodburl, 'mongodb://192.168.1.200:27017/')
        self.assertEqual(conf.collection, 'projects')
        self.assertDictEqual(conf.filterquery, {'is_private': {'$ne': True}})

    def test_path_marked_nofollow_can_have_arbitrary_substructure_3(self):
        """A path marked no-follow can have any and arbitrary substructure."""
        confp = YamlConfigParser()
        confp.add_rule('mongodburl')
        confp.add_rule('collection')
        confp.add_rule('filterquery', nofollow=True)
        conf = self._test_conf_good(confp, '''
        mongodburl: mongodb://192.168.1.200:27017/
        collection: projects
        filterquery: "{ is_private: { $ne: true } }"
        ''')
        self.assertEqual(conf.mongodburl, 'mongodb://192.168.1.200:27017/')
        self.assertEqual(conf.collection, 'projects')
        self.assertEqual(conf.filterquery, '{ is_private: { $ne: true } }')

    def test_path_marked_nofollow_can_be_optional_default_opt_good(self):
        """A path marked no-follow can also be optional or take defaults."""
        confp = YamlConfigParser()
        confp.add_rule('filterquery', optional=True, nofollow=True)
        conf = self._test_conf_good(confp, '{}')
        self.assertIsNone(conf.filterquery)

    def test_path_marked_nofollow_can_be_optional_default_noopt_bad(self):
        """A path marked no-follow can also be optional or take defaults."""
        confp = YamlConfigParser()
        confp.add_rule('filterquery', nofollow=True)
        self._test_conf_bad(
            confp=confp,
            conftext='{}',
            excrex='"filterquery" is missing')

    def test_path_marked_nofollow_can_be_optional_default_def_good(self):
        """A path marked no-follow can also be optional or take defaults."""
        confp = YamlConfigParser()
        confp.add_rule(
            'filterquery', nofollow=True, default={'is_private': {'$ne': True}})
        conf = self._test_conf_good(confp, '{}')
        self.assertIsInstance(conf.filterquery, dict)
        self.assertDictEqual(conf.filterquery, {'is_private': {'$ne': True}})

    def test_path_marked_nofollow_can_be_optional_default_nodef_bad(self):
        """A path marked no-follow can also be optional or take defaults."""
        confp = YamlConfigParser()
        confp.add_rule('filterquery', default={'is_private': {'$ne': True}})
        self._test_conf_bad(
            confp=confp,
            conftext='{}',
            excrex='"filterquery.is_private" unexpected by parser')

    def test_path_marked_nofollow_can_be_optional_default_optdef_bad(self):
        """A path marked no-follow can also be optional or take defaults."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError,
                '"filterquery" cannot be optional and have a default'):
            confp.add_rule(
                'filterquery', optional=True, nofollow=True,
                default={'is_private': {'$ne': True}})

    def test_path_marked_nofollow_cannot_have_subrules(self):
        """A path marked no-follow cannot have any subrules."""
        confp = YamlConfigParser()
        confp.add_rule('filterquery', nofollow=True)
        with self.assertRaisesRegex(
                ValueError,
                '"filterquery.is_private" is a descendant of a nofollow rule'):
            confp.add_rule('filterquery.is_private')


class TestPathTypeChecking(TestCase):
    """Check statements in "Path Type Checking"."""

    def test_ensure_field_is_str_int_bool_float_bad_1(self):
        """Ensure that a field is a str, int, bool, float, etc."""
        confp = YamlConfigParser()
        confp.add_rule('server.addr', path_type=str)
        confp.add_rule('server.port', path_type=int)
        self._test_conf_bad(
            confp=confp,
            conftext='''
            server:
              addr: ~
              port: 81
            ''',
            excrex='"server.addr" has type NoneType not type str')

    def test_ensure_field_is_str_int_bool_float_bad_2(self):
        """Ensure that a field is a str, int, bool, float, etc."""
        confp = YamlConfigParser()
        confp.add_rule('server.addr', path_type=str)
        confp.add_rule('server.port', path_type=int)
        self._test_conf_bad(
            confp=confp,
            conftext='''
            server:
              addr: 127.0.0.1
              port: "81"
            ''',
            excrex='"server.port" has type str not type int')

    def test_ensure_field_is_str_int_bool_float_good(self):
        """Ensure that a field is a str, int, bool, float, etc.

        This test includes Python 2/3-specific branches for the
        expansion of str and int types, and the removal of the unicode
        and long types.

        """
        # pylint: disable=undefined-variable # unicode/long for Python 2 support
        NoneType = type(None)
        confp = YamlConfigParser()
        confp.add_rule('bool_field', path_type=bool)
        confp.add_rule('str_field', path_type=str)
        if sys.version_info.major == 2:
            confp.add_rule('unicode_field', path_type=unicode)
        else:
            confp.add_rule('unicode_field', path_type=str)
        confp.add_rule('int_field', path_type=int)
        if sys.version_info.major == 2:
            confp.add_rule('long_field', path_type=long)
        else:
            confp.add_rule('long_field', path_type=int)
        confp.add_rule('float_field', path_type=float)
        confp.add_rule('date_field', path_type=date)
        confp.add_rule('datetime_field', path_type=datetime)
        confp.add_rule('dict_field', path_type=dict)
        confp.add_rule('list_field', path_type=list)
        confp.add_rule('nonetype_field', path_type=NoneType)
        conf = self._test_conf_good(confp, u'''
        bool_field: true
        str_field: "Hello world!"
        unicode_field: "Hεllo wØrld!"
        int_field: 42
        long_field: 9223372036854775808
        float_field: 1.e+5
        date_field: 2020-01-01
        datetime_field: 2020-01-01 02:03:04
        dict_field: {}
        list_field: []
        nonetype_field: ~
        ''')
        self.assertIsInstance(conf.bool_field, bool)
        self.assertIsInstance(conf.str_field, str)
        if sys.version_info.major == 2:
            self.assertIsInstance(conf.unicode_field, unicode)
        else:
            self.assertIsInstance(conf.unicode_field, str)
        self.assertIsInstance(conf.int_field, int)
        if sys.version_info.major == 2:
            self.assertIsInstance(conf.long_field, long)
        else:
            self.assertIsInstance(conf.long_field, int)
        self.assertIsInstance(conf.float_field, float)
        self.assertIsInstance(conf.date_field, date)
        self.assertIsInstance(conf.datetime_field, datetime)
        self.assertIsInstance(conf.dict_field, YamlConfig)
        self.assertIsInstance(conf.list_field, YamlConfigList)
        self.assertIsInstance(conf.nonetype_field, NoneType)

    def test_union_types_handle_complex_types_like_number_string_good_1(self):
        """Union types handle complex types like a number or a string."""
        confp = YamlConfigParser()
        confp.add_rule('server.timeout', path_type=(int, float))
        conf = self._test_conf_good(confp, '''
        server:
          timeout: 1.2
        ''')
        self.assertIsInstance(conf.server.timeout, float)
        self.assertEqual(conf.server.timeout, 1.2)

    def test_union_types_handle_complex_types_like_number_string_good_2(self):
        """Union types handle complex types like a number or a string."""
        confp = YamlConfigParser()
        confp.add_rule('server.timeout', path_type=(int, float))
        conf = self._test_conf_good(confp, '''
        server:
          timeout: 1
        ''')
        self.assertIsInstance(conf.server.timeout, int)
        self.assertEqual(conf.server.timeout, 1.0)

    def test_path_contains_a_map_or_a_list_map_good(self):
        """Ensure that a path contains a map or a list."""
        confp = YamlConfigParser()
        confp.add_rule('projects', path_type=dict)
        confp.add_rule('projects.*')
        conf = self._test_conf_good(confp, '''
        projects:
          ProjectX: "Project X is an eXtreme project (for more info talk to Alice)"
          meerkat_works: "Bob's not-quite skunkworks project"
        ''')
        self.assertIsInstance(conf.projects, YamlConfig)
        self.assertSetEqual(set(conf.projects), {'ProjectX', 'meerkat_works'})

    def test_path_contains_a_map_or_a_list_map_bad(self):
        """Ensure that a path contains a map or a list."""
        confp = YamlConfigParser()
        confp.add_rule('projects', path_type=dict)
        confp.add_rule('projects.*')
        self._test_conf_bad(
            confp=confp,
            conftext='''
            projects:
            - ProjectX
            - meerkat_works
            ''',
            excrex='"projects" has type list not type dict')

    def test_path_contains_a_map_or_a_list_list_good(self):
        """Ensure that a path contains a map or a list."""
        confp = YamlConfigParser()
        confp.add_rule('users', path_type=list)
        confp.add_rule('users.*')
        conf = self._test_conf_good(confp, '''
        users:
        - alice
        - bob
        - carol
        ''')
        self.assertIsInstance(conf.users, YamlConfigList)
        self.assertListEqual(list(conf.users), ['0', '1', '2'])

    def test_path_contains_a_map_or_a_list_list_bad(self):
        """Ensure that a path contains a map or a list."""
        confp = YamlConfigParser()
        confp.add_rule('users', path_type=list)
        confp.add_rule('users.*')
        self._test_conf_bad(
            confp=confp,
            conftext='''
            users:
              alice:  Alice A.
              bob:    Bob B.
              carol:  Carol C.
            ''',
            excrex='"users" has type dict not type list')

    def test_config_file_itself_is_a_list_or_map_list_good(self):
        """Ensure that a config file itself is a list or a map."""
        confp = YamlConfigParser(path_type=list)
        confp.add_rule('*.addr', path_type=str)
        confp.add_rule('*.port', path_type=int)
        conf = self._test_conf_good(confp, '''
        - addr: 192.0.2.200
          port: 81
        - addr: 192.0.2.201
          port: 81
        - addr: 198.51.100.15
          port: 8080
        - addr: 203.0.113.130
          port: 8080
        ''')
        self.assertIsInstance(conf, YamlConfigList)
        self.assertEqual(len(conf), 4)
        self.assertEqual(list(conf), ['0', '1', '2', '3'])
        self.assertEqual(conf[0].addr, '192.0.2.200')
        self.assertEqual(conf[0].port, 81)

    def test_config_file_not_atomic_element_bad_1(self):
        """A config file cannot be an atomic value; it must be a map or list."""
        confp = YamlConfigParser(path_type=int)
        self._test_conf_bad(
            confp=confp,
            conftext='42',
            excrex=r'config is a\(n\) int but a record or list is expected')

    def test_config_file_not_atomic_element_bad_2(self):
        """A config file cannot be an atomic value; it must be a map or list."""
        confp = YamlConfigParser(path_type=int)
        self._test_conf_bad(
            confp=confp,
            conftext='-42',
            excrex=r'config is a\(n\) int but a record or list is expected')

    def test_config_file_not_atomic_element_good_1(self):
        """A config file cannot be an atomic value; it must be a map or list."""
        confp = YamlConfigParser(path_type=dict)
        confp.add_rule('number', path_type=int)
        conf = self._test_conf_good(confp, 'number: 42')
        self.assertEqual(conf.number, 42)

    def test_config_file_not_atomic_element_good_2(self):
        """A config file cannot be an atomic value; it must be a map or list."""
        confp = YamlConfigParser(path_type=list)
        confp.add_rule('0', path_type=int)
        conf = self._test_conf_good(confp, '- 42')
        self.assertEqual(conf[0], 42)


class TestRuleTestFunctions(TestCase):
    """Check statements in "Rule Test Functions"."""

    def test_verify_value_matches_regex_good(self):
        """Verify that a value matches a regular expression."""
        confp = YamlConfigParser()
        confp.add_rule('username', test=test.is_regex('^[a-z][a-z0-9]*$'))
        conf = self._test_conf_good(confp, 'username: carol57')
        self.assertEqual(conf.username, 'carol57')

    def test_verify_value_matches_regex_bad(self):
        """Verify that a value matches a regular expression."""
        confp = YamlConfigParser()
        confp.add_rule('username', test=test.is_regex('^[a-z][a-z0-9]*$'))
        self._test_conf_bad(
            confp=confp,
            conftext='username: Carol C.',
            excrex=('"username" failed test: "Carol C." does not match ' +
                    r'/\^\[a-z\]\[a-z0-9\]\*\$'))

    def test_verify_value_is_ipv4_address_good(self):
        """Verify that a value is an IPv4 address."""
        confp = YamlConfigParser()
        confp.add_rule('server.addr', test=test.is_ipv4_address)
        conf = self._test_conf_good(confp, '''
        server:
          addr: 192.0.2.200
        ''')
        self.assertEqual(conf.server.addr, '192.0.2.200')

    def test_verify_value_is_ipv4_address_bad(self):
        """Verify that a value is an IPv4 address."""
        confp = YamlConfigParser()
        confp.add_rule('server.addr', test=test.is_ipv4_address)
        self._test_conf_bad(
            confp=confp,
            conftext='''
            server:
              addr: 452.34.256.193
            ''',
            excrex=('"server.addr" failed test: 1st octet of' +
                    ' "452.34.256.193" exceeds 255'))

    def test_functions_packages_within_yamlfig_good(self):
        """Test functions packaged within yamlfig."""
        dirpath = '{0}_dir'.format(self.testname)
        confp = YamlConfigParser()
        confp.add_rule('interval_field', test=test.is_interval(40, 50))
        confp.add_rule('regex_field', test=test.is_regex('[a-z]{5}'))
        confp.add_rule('ipv4_address_field', test=test.is_ipv4_address)
        confp.add_rule('domain_name_field', test=test.is_domain_name)
        confp.add_rule('email_address_field', test=test.is_email_address)
        confp.add_rule('url_field', test=test.is_url)
        confp.add_rule(
            'file_path_field', test=test.is_file_path('exists', 'isdir'))
        os.mkdir(dirpath)
        conf = self._test_conf_good(confp, '''
        interval_field: 42
        regex_field: ZZZaaaaaZZZ
        ipv4_address_field: 192.0.2.200
        domain_name_field: ftp.hr.example.com
        email_address_field: user@example.com
        url_field: http://example.com/search.php?q=term
        file_path_field: {0}
        '''.format(dirpath))
        self.assertEqual(conf.interval_field, 42)
        self.assertEqual(conf.regex_field, 'ZZZaaaaaZZZ')
        self.assertEqual(conf.domain_name_field, 'ftp.hr.example.com')
        self.assertEqual(conf.email_address_field, 'user@example.com')
        self.assertEqual(conf.url_field, 'http://example.com/search.php?q=term')
        self.assertEqual(conf.file_path_field, dirpath)

    def test_writing_own_test_functions_good(self):
        """Writing our own test functions."""
        # pylint: disable=unused-argument
        def has_default_and_user_fields(conf, path, value):
            if 'default' not in value:
                return '"default" field is missing'
            for field in value:
                if field != 'default' and not field.startswith('user-'):
                    return ('"{0}" is not "default" nor starts with "user-"'
                            .format(field))
            return None

        confp = YamlConfigParser()
        confp.add_rule('uploads', test=has_default_and_user_fields)
        confp.add_rule('uploads.*')

        conf = self._test_conf_good(confp, '''
        uploads:
          default:     /var/share/SomeApp/uploads
          user-alice:  /home/alice/uploads
          user-bob:    /home/bob/public
        ''')
        self.assertSetEqual(
            set(conf.uploads), {'default', 'user-alice', 'user-bob'})
        self.assertEqual(conf.uploads.default, '/var/share/SomeApp/uploads')
        self.assertEqual(conf.uploads['user-alice'], '/home/alice/uploads')
        self.assertEqual(conf.uploads['user-bob'], '/home/bob/public')

    def test_writing_own_test_functions_bad_1(self):
        """Writing our own test functions."""
        # pylint: disable=unused-argument
        def has_default_and_user_fields(conf, path, value):
            if 'default' not in value:
                return '"default" field is missing'
            for field in value:
                if field != 'default' and not field.startswith('user-'):
                    return ('"{0}" is not "default" nor starts with "user-"'
                            .format(field))
            return None

        confp = YamlConfigParser()
        confp.add_rule('uploads', test=has_default_and_user_fields)
        confp.add_rule('uploads.*')

        self._test_conf_bad(
            confp=confp,
            conftext='''
            uploads:
              user-alice:  /home/alice/uploads
              user-bob:    /home/bob/public
            ''',
            excrex='"uploads" failed test: "default" field is missing')

    def test_writing_own_test_functions_bad_2(self):
        """Writing our own test functions."""
        # pylint: disable=unused-argument
        def has_default_and_user_fields(conf, path, value):
            if 'default' not in value:
                return '"default" field is missing'
            for field in value:
                if field != 'default' and not field.startswith('user-'):
                    return ('"{0}" is neither "default" nor starts with "user-"'
                            .format(field))
            return None

        confp = YamlConfigParser()
        confp.add_rule('uploads', test=has_default_and_user_fields)
        confp.add_rule('uploads.*')

        self._test_conf_bad(
            confp=confp,
            conftext='''
            uploads:
              default:     /var/share/SomeApp/uploads
              alice:       /home/alice/uploads
            ''',
            excrex=('"uploads" failed test: "alice" is neither "default"' +
                    ' nor starts with "user-"'))


class TestCaveats(TestCase):
    """Check statements in "Rule Test Functions"."""

    def test_field_names_with_leading_underscores_warning_on(self):
        """Field names with leading underscores."""
        confp = YamlConfigParser()
        confp.add_rule('_field')

        self._write_file(self.conffile, '_field: aaaaa')

        # Enable warnings and confirm we get a warning that turns warnings off
        warning_off_orig = print_underscore_warning.off
        print_underscore_warning.off = False
        try:
            with CaptureIO('{0}_warn'.format(self.testname)) as capio:
                conf = confp.parse_file(self.conffile)
            stderr = capio.get_stderr()
            self.assertRegex(stderr, '.*Warning.*')
            self.assertTrue(print_underscore_warning.off)
        finally:
            print_underscore_warning.off = warning_off_orig
        self.assertListEqual(list(conf), ['_field'])
        self.assertEqual(conf['_field'], 'aaaaa')

    def test_field_names_with_leading_underscores_warning_off(self):
        """Field names with leading underscores."""
        confp = YamlConfigParser()
        confp.add_rule('_field')

        self._write_file(self.conffile, '_field: aaaaa')

        # Disable warnings and confirm the warning is suppressed
        warning_off_orig = print_underscore_warning.off
        print_underscore_warning.off = True
        try:
            with CaptureIO('{0}_nowarn'.format(self.testname)) as capio:
                _ = confp.parse_file(self.conffile)
            stderr = capio.get_stderr()
            self.assertEqual(stderr, '')
        finally:
            print_underscore_warning.off = warning_off_orig
