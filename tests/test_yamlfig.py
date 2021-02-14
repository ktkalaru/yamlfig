# -*- coding: utf-8 -*-

"""Conduct comprehensive unit-test of package functionality."""

# pylint: disable=too-many-lines, import-error, too-many-public-methods
# pylint: disable=line-too-long

from __future__ import print_function, absolute_import

# Standard modules
import itertools
import math
import os
import random
import sre_constants
import sys

from datetime import date, datetime

# Installed packages
import yaml
import unittest2

# Shared testing basics - pytest enables the relative load
from testbase import CaptureIO, TestCase, _as_naive_datetime_in_utc

# Target package for testing
from yamlfig import YamlConfigParser, YamlConfigRule, YamlConfig, \
    YamlConfigList, ParseError, test, print_underscore_warning


class ParserChecks(TestCase):
    """Check that parser construction behaves as designed."""

    def test_parser_root_rule_rule_path_bad(self):
        """Root rule should not have a rule path."""
        with self.assertRaisesRegex(
                ValueError, 'Root rule cannot have a rule path "field"'):
            YamlConfigParser(rule_path='field')

    def test_parser_nonroot_rule_no_rule_path_bad_1(self):
        """Non-root rule should always have a rule path."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError, 'Non-root rule must have a rule path'):
            YamlConfigRule(root=confp)

    def test_parser_nonroot_rule_no_rule_path_bad_2(self):
        """Non-root rule should always have a rule path."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError, 'Non-root rule must have a rule path'):
            confp.add_rule(None)

    def test_parser_field_name_bad_1(self):
        """Empty rule paths should raise error."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(ValueError, '"" is missing a field name'):
            confp.add_rule('')

    def test_parser_field_name_bad_2(self):
        """Empty fields in rule paths should raise error."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError, '"." is missing a field name'):
            confp.add_rule('.')

    def test_parser_field_name_bad_3(self):
        """Empty fields in rule paths should raise error."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError, '".field" is missing a field name'):
            confp.add_rule('.field')

    def test_parser_field_name_bad_4(self):
        """Empty fields in rule paths should raise error."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError, '"field." is missing a field name'):
            confp.add_rule('field.')

    def test_parser_field_name_bad_5(self):
        """Empty fields in rule paths should raise error."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError, '"field..field" is missing a field name'):
            confp.add_rule('field..field')

    def test_parser_wildcard_partial_matches_bad_1(self):
        """Wildcard partial matches should raise error."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError, r'"field\*" cannot use a partial wildcard'):
            confp.add_rule('field*')

    def test_parser_wildcard_partial_matches_bad_2(self):
        """Wildcard partial matches should raise error."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError, r'"\*field" cannot use a partial wildcard'):
            confp.add_rule('*field')

    def test_parser_wildcard_partial_matches_bad_3(self):
        """Wildcard partial matches should raise error."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError, r'"fie\*ld" cannot use a partial wildcard'):
            confp.add_rule('fie*ld')

    def test_parser_wildcard_partial_matches_bad_4(self):
        """Wildcard partial matches should raise error."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError,
                r'"field.part\*.field" cannot use a partial wildcard'):
            confp.add_rule('field.part*.field')

    def test_parser_wildcard_preceding_fixed_path_bad_1(self):
        """Wildcard rules preceding fixed-path siblings should raise error."""
        confp = YamlConfigParser()
        confp.add_rule('*')
        with self.assertRaisesRegex(
                ValueError, '"field" cannot follow a wildcard rule'):
            confp.add_rule('field')

    def test_parser_wildcard_preceding_fixed_path_bad_2(self):
        """Wildcard rules preceding fixed-path siblings should raise error."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.*')
        with self.assertRaisesRegex(
                ValueError,
                '"aaa.aaa.field" cannot follow a wildcard rule'):
            confp.add_rule('aaa.aaa.field')

    def test_parser_wildcard_preceding_fixed_path_bad_3(self):
        """Wildcard rules preceding fixed-path siblings should raise error."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.*.aaa')
        with self.assertRaisesRegex(
                ValueError,
                '"aaa.field" cannot follow a wildcard rule'):
            confp.add_rule('aaa.field.aaa')

    def test_parser_fixed_path_preceding_wildcard_good_1(self):
        """Wildcard rules following fixed-path siblings should be supported."""
        # pylint: disable=no-self-use
        confp = YamlConfigParser()
        confp.add_rule('field')
        confp.add_rule('*')

    def test_parser_fixed_path_preceding_wildcard_good_2(self):
        """Wildcard rules following fixed-path siblings should be supported."""
        # pylint: disable=no-self-use
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.field')
        confp.add_rule('aaa.aaa.*')

    def test_parser_fixed_path_preceding_wildcard_good_3(self):
        """Wildcard rules following fixed-path siblings should be supported."""
        # pylint: disable=no-self-use
        confp = YamlConfigParser()
        confp.add_rule('aaa.field.aaa')
        confp.add_rule('aaa.*.aaa')

    def test_parser_nonstr_rule_paths_good_1(self):
        """String and unicode rule paths should be supported."""
        # pylint: disable=no-self-use
        confp = YamlConfigParser()
        confp.add_rule('str_rule_path')

    def test_parser_nonstr_rule_paths_good_2(self):
        """String and unicode rule paths should be supported."""
        # pylint: disable=no-self-use
        confp = YamlConfigParser()
        confp.add_rule('str_rule_path.subfield.subsubfield')

    def test_parser_nonstr_rule_paths_good_3(self):
        """String and unicode rule paths should be supported."""
        # pylint: disable=no-self-use
        confp = YamlConfigParser()
        confp.add_rule('str rule with spaces.sub-field with spaces')

    def test_parser_nonstr_rule_paths_good_4(self):
        """String and unicode rule paths should be supported."""
        # pylint: disable=no-self-use
        confp = YamlConfigParser()
        confp.add_rule(u'unicode_rule_path')

    def test_parser_nonstr_rule_paths_good_5(self):
        """String and unicode rule paths should be supported."""
        # pylint: disable=no-self-use
        confp = YamlConfigParser()
        confp.add_rule(u'unicode_rule_path.subfield.subsubfield')

    def test_parser_nonstr_rule_paths_good_6(self):
        """String and unicode rule paths should be supported."""
        # pylint: disable=no-self-use
        confp = YamlConfigParser()
        confp.add_rule(u'unicode rule with spaces.sub-field with spaces')

    def test_parser_nonstr_rule_paths_bad_1(self):
        """Integer rules should raise error."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError, r'42 is a\(n\) int not a str'):
            confp.add_rule(42)

    def test_parser_nonstr_rule_paths_bad_2(self):
        """Boolean rules should raise error."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError, r'True is a\(n\) bool not a str'):
            confp.add_rule(True)

    def test_parser_nonstr_rule_paths_bad_3(self):
        """Float rules should raise error."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError, r'0\.0 is a\(n\) float not a str'):
            confp.add_rule(0.0)

    def test_parser_duplicate_rule_paths_bad_1(self):
        """Duplicate rule paths should raise error."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        with self.assertRaisesRegex(
                ValueError, '"aaa" cannot be defined multiple times'):
            confp.add_rule('aaa')

    def test_parser_duplicate_rule_paths_bad_2(self):
        """Duplicate rule paths should raise error."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        with self.assertRaisesRegex(
                ValueError, '"aaa.aaa.aaa" cannot be defined multiple times'):
            confp.add_rule('aaa.aaa.aaa')

    def test_parser_overlapping_implicit_rule_paths_good(self):
        """Overlapping implicit rule paths should not raise error."""
        # pylint: disable=no-self-use
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.aaa.bbb')
        confp.add_rule('aaa.bbb.aaa')
        confp.add_rule('aaa.bbb.bbb')

    def test_parser_duplicate_implicit_rule_paths_bad_1(self):
        """A rule path already implicitly added should raise error."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa.aaa')
        with self.assertRaisesRegex(
                ValueError, '"aaa" cannot be defined multiple times'):
            confp.add_rule('aaa')

    def test_parser_duplicate_implicit_rule_paths_bad_2(self):
        """A rule path already implicitly added should raise error."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa.aaa')
        with self.assertRaisesRegex(
                ValueError, '"aaa.aaa" cannot be defined multiple times'):
            confp.add_rule('aaa.aaa')

    def test_parser_duplicate_implicit_rule_paths_bad_3(self):
        """A rule path already implicitly added should raise error."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa.aaa')
        with self.assertRaisesRegex(
                ValueError, '"aaa.aaa.aaa" cannot be defined multiple times'):
            confp.add_rule('aaa.aaa.aaa')

    def test_parser_root_optional_bad_1(self):
        """Optional root rule should raise error."""
        with self.assertRaisesRegex(
                ValueError, 'Root rule cannot be optional'):
            YamlConfigParser(optional=True)

    def test_parser_root_optional_bad_2(self):
        """Optional root rule should raise error."""
        with self.assertRaisesRegex(
                ValueError, 'Root rule cannot be optional'):
            YamlConfigParser(optional=True, nofollow=True)

    def test_parser_root_default_bad_1(self):
        """Default root rule should raise error."""
        with self.assertRaisesRegex(
                ValueError, 'Root rule cannot take a default value'):
            YamlConfigParser(default={'aaa': 'aaaaa'})

    def test_parser_root_default_bad_2(self):
        """Default root rule should raise error."""
        with self.assertRaisesRegex(
                ValueError, 'Root rule cannot take a default value'):
            YamlConfigParser(default={'aaa': 'aaaaa'}, nofollow=True)

    def test_parser_rule_optional_and_default_bad_1(self):
        """A rule that is both optional and default should raise error."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError, '"field" cannot be optional and have a default'):
            confp.add_rule('field', optional=True, default={'field': 'aaaaa'})

    def test_parser_rule_optional_and_default_bad_2(self):
        """A rule that is both optional and default should raise error."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError, '"a.a.a" cannot be optional and have a default'):
            confp.add_rule('a.a.a', optional=True, default={'field': 'aaaaa'})

    def test_parser_nofollow_rule_subrules_bad_1(self):
        """Adding a subrule to a nofollow rule should raise error."""
        confp = YamlConfigParser(nofollow=True)
        with self.assertRaisesRegex(
                ValueError, '"field" is a descendant of a nofollow rule'):
            confp.add_rule('field')

    def test_parser_nofollow_rule_subrules_bad_2(self):
        """Adding a subrule to a nofollow rule should raise error."""
        confp = YamlConfigParser()
        confp.add_rule('aaa', nofollow=True)
        with self.assertRaisesRegex(
                ValueError, '"aaa.aaa" is a descendant of a nofollow rule'):
            confp.add_rule('aaa.aaa')

    def test_parser_nofollow_rule_subrules_bad_3(self):
        """Adding a subrule to a nofollow rule should raise error."""
        confp = YamlConfigParser()
        confp.add_rule('aaa', nofollow=True)
        with self.assertRaisesRegex(
                ValueError, '"aaa.aaa.aaa" is a descendant of a nofollow rule'):
            confp.add_rule('aaa.aaa.aaa')

    def test_parser_nofollow_rule_siblings_good(self):
        """Adding siblings of a nofollow rule should not raise error."""
        # pylint: disable=no-self-use
        confp = YamlConfigParser()
        confp.add_rule('aaa', nofollow=True)
        confp.add_rule('bbb')
        confp.add_rule('ccc.aaa.aaa')

    def test_parser_non_type_path_type_bad(self):
        """Specifying path_type that is not a type should raise error."""
        conf = YamlConfigParser()
        with self.assertRaisesRegex(
                ValueError, r'"field" path_type is a\(n\) str not a type'):
            conf.add_rule('field', path_type='str')


class ParsedYamlTypes(TestCase):
    """Check that we can handle all the types that SafeLoader supports.

    The types were collected from the pyyaml/constructor.py source:
      https://github.com/yaml/pyyaml/blob/master/lib/yaml/constructor.py

    The following caveats apply:
    - Lacking use cases for base-60 float/integer thing so skipping for now.
    - Timezone-aware timestamps are only lightly and awkwardly tested.
    """

    def test_yaml_parsed_types_null(self):
        """Test recognition of various forms of null value."""
        confp = YamlConfigParser()

        none_type = type(None)
        confp.add_rule('yaml_empty', path_type=none_type)
        confp.add_rule('yaml_canonical', path_type=none_type)
        confp.add_rule('yaml_null', path_type=none_type)
        confp.add_rule('yaml_list', path_type=list)
        confp.add_rule('yaml_list.*', path_type=none_type)
        confp.add_rule('yaml_map', path_type=dict)
        confp.add_rule('yaml_map.*')

        self._write_file(self.conffile, """
          yaml_empty:
          yaml_canonical: ~
          yaml_null: null
          yaml_list:
          - ~
          -
          - null
          yaml_map:
            aaaaa: ~
            ~: bbbbb
            ? ccccc
        """)

        conf = confp.parse_file(self.conffile)

        self.assertIsNone(conf.yaml_empty)
        self.assertIsNone(conf.yaml_canonical)
        self.assertIsNone(conf.yaml_null)
        self.assertIsNone(conf.yaml_list[0])
        self.assertIsNone(conf.yaml_list[1])
        self.assertIsNone(conf.yaml_list[2])
        self.assertSetEqual(set(conf.yaml_map), set(['aaaaa', None, 'ccccc']))
        self.assertIsNone(conf.yaml_map['aaaaa'])
        self.assertEqual(conf.yaml_map[None], 'bbbbb')
        self.assertIsNone(conf.yaml_map['ccccc'])

    def test_yaml_parsed_types_bool(self):
        """Test recognition of various forms of boolean value."""
        confp = YamlConfigParser()

        confp.add_rule('yaml_bool.true_syms.*', path_type=bool)
        confp.add_rule('yaml_bool.false_syms.*', path_type=bool)

        self._write_file(self.conffile, """
          yaml_bool:
            true_syms:
            - True
            - yes
            - true
            - on
            false_syms:
            - False
            - no
            - false
            - off
        """)

        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.yaml_bool.true_syms[0], True)
        self.assertEqual(conf.yaml_bool.true_syms[1], True)
        self.assertEqual(conf.yaml_bool.true_syms[2], True)
        self.assertEqual(conf.yaml_bool.true_syms[3], True)
        self.assertEqual(conf.yaml_bool.false_syms[0], False)
        self.assertEqual(conf.yaml_bool.false_syms[1], False)
        self.assertEqual(conf.yaml_bool.false_syms[2], False)
        self.assertEqual(conf.yaml_bool.false_syms[3], False)

    def test_yaml_parsed_types_int(self):
        """Test recognition of various forms of integer."""
        confp = YamlConfigParser()

        confp.add_rule('yaml_int.decimal', path_type=int)
        confp.add_rule('yaml_int.binary', path_type=int)
        confp.add_rule('yaml_int.hexadecimal', path_type=int)
        confp.add_rule('yaml_int.octal', path_type=int)

        self._write_file(self.conffile, """
          yaml_int:
            decimal: 12345
            binary: 0b1111
            hexadecimal: 0xdeadbeef
            octal: 0755
        """)

        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.yaml_int.decimal, 12345)
        self.assertEqual(conf.yaml_int.binary, 15)
        self.assertEqual(conf.yaml_int.hexadecimal, 3735928559)
        self.assertEqual(conf.yaml_int.octal, 493)

    def test_yaml_parsed_types_float(self):
        """Test recognition of various forms of floating point value."""
        confp = YamlConfigParser()

        confp.add_rule('yaml_float.smallval', path_type=float)
        confp.add_rule('yaml_float.bigval', path_type=float)
        confp.add_rule('yaml_float.negval', path_type=float)
        confp.add_rule('yaml_float.infval', path_type=float)
        confp.add_rule('yaml_float.nanval', path_type=float)

        self._write_file(self.conffile, """
          yaml_float:
            smallval: 123.0e-5
            bigval: 456.0e+5
            negval: -789.0e-2
            infval: .inf
            nanval: .nan
        """)

        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.yaml_float.smallval, 0.00123)
        self.assertEqual(conf.yaml_float.bigval, 45600000.0)
        self.assertEqual(conf.yaml_float.negval, -7.89)
        self.assertTrue(math.isinf(conf.yaml_float.infval))
        self.assertTrue(math.isnan(conf.yaml_float.nanval))

    def test_yaml_parsed_types_timestamps(self):
        """Test recognition of various forms of timestamp."""
        confp = YamlConfigParser()

        confp.add_rule('yaml_time.date', path_type=date)
        confp.add_rule('yaml_time.datetime', path_type=datetime)
        confp.add_rule('yaml_time.tzdatetime', path_type=datetime)

        self._write_file(self.conffile, """
          yaml_time:
            date: 2020-01-01
            datetime: 2020-01-01 02:03:04
            tzdatetime: 2019-12-31 14:03:04-12:00
        """)

        conf = confp.parse_file(self.conffile)

        # Confirm yaml_time dates and datetimes are parsed as objects
        self.assertEqual(conf.yaml_time.date, date(2020, 1, 1))
        self.assertEqual(conf.yaml_time.datetime, datetime(2020, 1, 1, 2, 3, 4))
        self.assertEqual(
            _as_naive_datetime_in_utc(conf.yaml_time.tzdatetime),
            datetime(2020, 1, 1, 2, 3, 4))

    def test_yaml_parsed_types_binary(self):
        """Test encoded binary values are recognized as str/bytes type.

        Byte sequences have type str in Python 2 and bytes in
        Python 3

        """
        confp = YamlConfigParser()

        if sys.version_info.major == 2:
            confp.add_rule('yaml_bin', path_type=str)
        else:
            confp.add_rule('yaml_bin', path_type=bytes)

        self._write_file(self.conffile, """
          yaml_bin: !!binary |
            ABEiM0RVZneImaq7zN3u/w==
        """)

        conf = confp.parse_file(self.conffile)

        decodedints = [
            0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77,
            0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff]
        if sys.version_info.major == 2:
            self.assertListEqual([ord(ch) for ch in conf.yaml_bin], decodedints)
        else:
            self.assertListEqual(list(conf.yaml_bin), decodedints)

    def test_yaml_parsed_types_string(self):
        """Test behavior of ascii and unicode strings in YAML.

        In Python 2, since neither str nor unicode inherit from the
        other, this means that a parser with path_type=str will raise
        a parse error on a config file with a unicode string, and
        likewise a parser with path_type=unicode will raise a parse
        error on a config file with a regular ascii string.

        In Python 3, values with ascii or unicode characters should
        be recognized with path_type=str
        """
        # pylint: disable=undefined-variable

        confp = YamlConfigParser()

        confp.add_rule('yaml_ascii', path_type=str)
        if sys.version_info.major == 2:
            confp.add_rule('yaml_unicode', path_type=unicode)
        else:
            confp.add_rule('yaml_unicode', path_type=str)

        self._write_file(self.conffile, u"""
          yaml_ascii: "Hello world!"
          yaml_unicode: "Hεllo wØrld!"
        """)

        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.yaml_ascii, 'Hello world!')
        self.assertEqual(conf.yaml_unicode, u'Hεllo wØrld!')

    def test_yaml_parsed_mapping(self):
        """Test that mapping values are recognized as dicts."""
        # Check that implicit and explicit mappings are converted to
        # YamlConfig objects and can be accessed as usual.
        confp = YamlConfigParser()

        confp.add_rule('yaml_record', path_type=dict)
        confp.add_rule('yaml_record.keyA', path_type=dict)
        confp.add_rule('yaml_record.keyA.subkey1', path_type=str)
        confp.add_rule('yaml_record.keyA.subkey2', path_type=str)
        confp.add_rule('yaml_record.keyB', path_type=dict)
        confp.add_rule('yaml_record.keyB.subkey1', path_type=str)
        confp.add_rule('yaml_record.keyB.subkey2', path_type=str)

        confp.add_rule('yaml_map', path_type=dict)
        confp.add_rule('yaml_map.keyA', path_type=dict)
        confp.add_rule('yaml_map.keyA.subkey1', path_type=str)
        confp.add_rule('yaml_map.keyA.subkey2', path_type=str)
        confp.add_rule('yaml_map.keyB', path_type=dict)
        confp.add_rule('yaml_map.keyB.subkey1', path_type=str)
        confp.add_rule('yaml_map.keyB.subkey2', path_type=str)

        self._write_file(self.conffile, """
          yaml_record:
            keyA:
              subkey1: aaaaa
              subkey2: bbbbb
            keyB:
              subkey1: ccccc
              subkey2: ddddd
          yaml_map: !!map
            keyA: !!map
              subkey1: aaaaa
              subkey2: bbbbb
            keyB: !!map
              subkey1: ccccc
              subkey2: ddddd
        """)

        conf = confp.parse_file(self.conffile)

        self.assertIsInstance(conf.yaml_record, YamlConfig)
        self.assertIsInstance(conf.yaml_record.keyA, YamlConfig)
        self.assertIsInstance(conf.yaml_record.keyB, YamlConfig)
        self.assertIsInstance(conf.yaml_map, YamlConfig)
        self.assertIsInstance(conf.yaml_map.keyA, YamlConfig)
        self.assertIsInstance(conf.yaml_map.keyB, YamlConfig)

        self.assertEqual(conf.yaml_record.keyA.subkey1, 'aaaaa')
        self.assertEqual(conf.yaml_record.keyA.subkey2, 'bbbbb')
        self.assertEqual(conf.yaml_record.keyB.subkey1, 'ccccc')
        self.assertEqual(conf.yaml_record.keyB.subkey2, 'ddddd')
        self.assertEqual(conf.yaml_map.keyA.subkey1, 'aaaaa')
        self.assertEqual(conf.yaml_map.keyA.subkey2, 'bbbbb')
        self.assertEqual(conf.yaml_map.keyB.subkey1, 'ccccc')
        self.assertEqual(conf.yaml_map.keyB.subkey2, 'ddddd')

    def test_yaml_parsed_map_nonstr_keys(self):
        """Test that mapping values with non-string keys are supported.

        Handling such key values during and after the parsing process
        can be more challenging since they cannot be matched by any
        rule path other than a wildcard, and once parsed, they cannot
        be accessed as attributes of the conf object.  Still, they are
        allowed in config files and can be managed.

        Note that strings containing unicode values are handled as a
        separate type in Python 2.

        """
        # pylint: disable=undefined-variable

        # Check that non-string keys are handled, and that usual
        # hashing is used via collisions

        confp = YamlConfigParser()

        confp.add_rule('yaml_record', path_type=dict)

        if sys.version_info.major == 2:
            confp.add_rule('yaml_record.*', path_type=(str, unicode))
        else:
            confp.add_rule('yaml_record.*', path_type=str)

        self._write_file(self.conffile, u"""
          yaml_record:
            ~: "None Key Value"

            42: "overwritten"
            42.0: "42 Key Value"

            "42": "'42' Key Value"

            0: "overwritten"
            False: "0 Key Value"

            1.0: "overwritten"
            True: "1.0 Key Value"

            key: "'key' Value"
            kεy: "'kεy' Value"

            "The Key": "'The Key' Value"

        """)

        conf = confp.parse_file(self.conffile)

        self.assertSetEqual(
            set(conf.yaml_record),
            set([None, 42, "42", 0, 1.0, 'key', u'kεy', 'The Key']))

        self.assertEqual(conf.yaml_record[None], 'None Key Value')
        self.assertEqual(conf.yaml_record[42], '42 Key Value')
        self.assertEqual(conf.yaml_record['42'], "'42' Key Value")
        self.assertEqual(conf.yaml_record[0], '0 Key Value')
        self.assertEqual(conf.yaml_record[1.0], '1.0 Key Value')
        self.assertEqual(conf.yaml_record['key'], "'key' Value")
        self.assertEqual(conf.yaml_record[u'kεy'], u"'kεy' Value")
        self.assertEqual(conf.yaml_record['The Key'], "'The Key' Value")

    def test_yaml_parsed_map_fieldorder(self):
        """Test that field order is determined by parser not config file.

        Additionally, this test tracks versions of python for which
        fields matched by wildcard rules are returned in the order
        they appear in the config file.  Since individual tests might
        fail, the test is run repeatedly, each with a random ordering
        of the fields in the config file.

        Note that returning the fields in the order they appear in the
        config file is probably actually a good thing, but this test
        is tracking actual behavior regardless of desired behavior:
        for earlier versions of python, the ordering is not
        consistent.

        """
        # pylint: disable=too-many-locals
        test_run_count = 5
        test_run_ordered = 0
        chars = ['s', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        for test_run in range(test_run_count):
            conffile = '{0}_test_run_{1}.yaml'.format(self.testname, test_run)

            # Generate a shuffled ordering of fields for the config file
            chars_config = chars[:]
            random.shuffle(chars_config)
            fields_config = ['field_{0}'.format(ch) for ch in chars_config]
            values = ['{0}'.format(ch)*5 for ch in chars_config]

            # Generate a sorted ordering of fields for the rules
            chars_rules = chars[:]
            fields_rules = ['field_{0}'.format(ch) for ch in chars_rules]

            # Construct the config from these orderings
            conftext = '\n'.join(
                ['{0}: {1}'.format(field, value)
                 for field, value
                 in zip(fields_config, values)])

            self._write_file(conffile, conftext)

            # Make and validate the fixed-rule parser's ordered fields
            confp_fixed = YamlConfigParser()
            for field in fields_rules:
                confp_fixed.add_rule(field)
            conf_fixed = confp_fixed.parse_file(conffile)
            self.assertListEqual(list(conf_fixed), fields_rules)

            # Make and validate the wildcard-rule conf parser's unordered fields
            confp_wild = YamlConfigParser()
            confp_wild.add_rule('*')
            conf_wild = confp_wild.parse_file(conffile)
            self.assertSetEqual(set(conf_wild), set(fields_rules))

            # In theory this next test could fail, if just by chance,
            # the wildcard version happened to return the results in
            # the order that they appeared in the config file, which
            # is why we rerun this test a few times in the event of a
            # failure, greatly reducing the probability of a chance
            # failure.
            if list(conf_wild) == fields_config:
                test_run_ordered += 1

        if(sys.version_info.major == 2 or
           (sys.version_info.major == 3 and sys.version_info.minor < 6)):
            self.assertLess(
                test_run_ordered, test_run_count,
                msg=(
                    'The order of fields in the wildcard version match the' +
                    ' order of the fields in the config file {0} times out' +
                    ' of {1} which is extremely unlikely to happen by' +
                    ' chance.  We appear to be  running on a version of' +
                    ' python that returns dict keys in insertion order,' +
                    ' which corresponds to order of appearance in the YAML' +
                    ' config file.  Please let the maintaner know.\n\n' +
                    'version: {2}').format(
                        test_run_ordered, test_run_count, sys.version))
        else:
            self.assertEqual(
                test_run_ordered, test_run_count,
                msg=(
                    'The order of fields in the wildcard version only match' +
                    ' the order of the fields in the config file {0}' +
                    ' times out of {1}.  This version of python was' +
                    ' understood to dict keys in insertion order, such' +
                    ' that they would be returned in the order in which' +
                    ' they appeared in the config file, but that is not' +
                    ' the case.  Please let the maintainer know.\n\n' +
                    'version: {2}').format(
                        test_run_ordered, test_run_count, sys.version))

    def test_yaml_parsed_types_seq(self):
        """Test sequences are recognized as lists."""
        # Check that implicit and explicit mappings are converted to
        # YamlConfigList objects and can be accessed as usual.
        confp = YamlConfigParser()

        confp.add_rule('yaml_lists', path_type=list)
        confp.add_rule('yaml_lists.0', path_type=list)
        confp.add_rule('yaml_lists.0.*', path_type=str)
        confp.add_rule('yaml_lists.1', path_type=list)
        confp.add_rule('yaml_lists.1.*', path_type=str)

        confp.add_rule('yaml_seqs', path_type=list)
        confp.add_rule('yaml_seqs.0', path_type=list)
        confp.add_rule('yaml_seqs.0.*', path_type=str)
        confp.add_rule('yaml_seqs.1', path_type=list)
        confp.add_rule('yaml_seqs.1.*', path_type=str)

        self._write_file(self.conffile, """
          yaml_lists:
            - - aaaaa
              - bbbbb
              - ccccc
            -
              - ddddd
              - eeeee
              - fffff
          yaml_seqs: !!seq
            - !!seq
              - aaaaa
              - bbbbb
              - ccccc
            - !!seq
              - ddddd
              - eeeee
              - fffff
        """)

        conf = confp.parse_file(self.conffile)

        self.assertIsInstance(conf.yaml_lists, YamlConfigList)
        self.assertIsInstance(conf.yaml_lists[0], YamlConfigList)
        self.assertIsInstance(conf.yaml_lists[1], YamlConfigList)
        self.assertIsInstance(conf.yaml_seqs, YamlConfigList)
        self.assertIsInstance(conf.yaml_seqs[0], YamlConfigList)
        self.assertIsInstance(conf.yaml_seqs[1], YamlConfigList)

        self.assertEqual(conf.yaml_lists[0][0], 'aaaaa')
        self.assertEqual(conf.yaml_lists[0][1], 'bbbbb')
        self.assertEqual(conf.yaml_lists[0][2], 'ccccc')
        self.assertEqual(conf.yaml_lists[1][0], 'ddddd')
        self.assertEqual(conf.yaml_lists[1][1], 'eeeee')
        self.assertEqual(conf.yaml_lists[1][2], 'fffff')

    def test_yaml_parsed_types_pairs(self):
        """Test pairs are recognized as lists.

        Note that since the !!pairs and !!omap types are effectively
        converted to lists of pairs, they get turned into lists of
        length-2 lists, and are effectively equivalent.  Also note
        that the underlying YAML parser itself treats them the same,
        in that duplicate keys are allowed for !!omap types for
        performance reasons.  (This test exists partly as a canary in
        case that ever changes.)

        """
        confp = YamlConfigParser()

        confp.add_rule('yaml_raw', path_type=list)
        confp.add_rule('yaml_raw.*', path_type=dict)
        confp.add_rule('yaml_raw.*.*', path_type=str)

        confp.add_rule('yaml_pairs', path_type=list)
        confp.add_rule('yaml_pairs.*', path_type=list)
        confp.add_rule('yaml_pairs.*.0', path_type=str)
        confp.add_rule('yaml_pairs.*.1', path_type=str)

        confp.add_rule('yaml_omap', path_type=list)
        confp.add_rule('yaml_omap.*', path_type=list)
        confp.add_rule('yaml_omap.*.0', path_type=str)
        confp.add_rule('yaml_omap.*.1', path_type=str)

        confp.add_rule('yaml_omap_dup', path_type=list)
        confp.add_rule('yaml_omap_dup.*', path_type=list)
        confp.add_rule('yaml_omap_dup.*.0', path_type=str)
        confp.add_rule('yaml_omap_dup.*.1', path_type=str)

        self._write_file(self.conffile, """
          yaml_raw:
          - aaa: xxx
          - bbb: yyy
          - ccc: zzz
          yaml_pairs: !!pairs
          - aaa: xxx
          - bbb: yyy
          - ccc: zzz
          yaml_omap: !!omap
          - aaa: xxx
          - bbb: yyy
          - ccc: zzz
          yaml_omap_dup: !!omap
          - aaa: www
          - aaa: xxx
          - bbb: yyy
          - ccc: zzz
        """)

        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.yaml_raw[0].aaa, 'xxx')
        self.assertEqual(conf.yaml_raw[1].bbb, 'yyy')
        self.assertEqual(conf.yaml_raw[2].ccc, 'zzz')

        self.assertEqual(conf.yaml_pairs[0][0], 'aaa')
        self.assertEqual(conf.yaml_pairs[0][1], 'xxx')
        self.assertEqual(conf.yaml_pairs[1][0], 'bbb')
        self.assertEqual(conf.yaml_pairs[1][1], 'yyy')
        self.assertEqual(conf.yaml_pairs[2][0], 'ccc')
        self.assertEqual(conf.yaml_pairs[2][1], 'zzz')

        self.assertEqual(conf.yaml_omap[0][0], 'aaa')
        self.assertEqual(conf.yaml_omap[0][1], 'xxx')
        self.assertEqual(conf.yaml_omap[1][0], 'bbb')
        self.assertEqual(conf.yaml_omap[1][1], 'yyy')
        self.assertEqual(conf.yaml_omap[2][0], 'ccc')
        self.assertEqual(conf.yaml_omap[2][1], 'zzz')

        self.assertEqual(conf.yaml_omap_dup[0][0], 'aaa')
        self.assertEqual(conf.yaml_omap_dup[0][1], 'www')
        self.assertEqual(conf.yaml_omap_dup[1][0], 'aaa')
        self.assertEqual(conf.yaml_omap_dup[1][1], 'xxx')
        self.assertEqual(conf.yaml_omap_dup[2][0], 'bbb')
        self.assertEqual(conf.yaml_omap_dup[2][1], 'yyy')
        self.assertEqual(conf.yaml_omap_dup[3][0], 'ccc')
        self.assertEqual(conf.yaml_omap_dup[3][1], 'zzz')

    def test_yaml_parsed_types_set(self):
        """Test sets are converted to lists and null-value maps to dicts."""
        confp = YamlConfigParser()

        confp.add_rule('yaml_nullmap', path_type=dict)
        confp.add_rule('yaml_nullmap.*', path_type=type(None))
        confp.add_rule('yaml_set', path_type=list)
        confp.add_rule('yaml_set.*', path_type=str)

        self._write_file(self.conffile, """
          yaml_nullmap:
            ? aaaaa
            ? bbbbb
            ? ccccc
          yaml_set: !!set
            ? aaaaa
            ? bbbbb
            ? ccccc
        """)

        conf = confp.parse_file(self.conffile)

        # In both cases, the order of the keys and list elements is
        # arbitrary and not necessarily the same as in the file, so
        # sets are used for validation.

        self.assertSetEqual(
            set(conf.yaml_nullmap),
            {'aaaaa', 'bbbbb', 'ccccc'})
        self.assertIsNone(conf.yaml_nullmap.aaaaa)
        self.assertIsNone(conf.yaml_nullmap.bbbbb)
        self.assertIsNone(conf.yaml_nullmap.ccccc)

        self.assertListEqual(list(conf.yaml_set), ['0', '1', '2'])
        self.assertSetEqual(
            {conf.yaml_set[idx] for idx in conf.yaml_set},
            {'aaaaa', 'bbbbb', 'ccccc'})

    def test_yaml_parsed_types_anchorrefs(self):
        """Test anchors, references, and merges are handled under the hood."""
        confp = YamlConfigParser()

        confp.add_rule('standard', path_type=dict)
        confp.add_rule('standard.aaaaa', path_type=str)
        confp.add_rule('standard.bbbbb', path_type=str)
        confp.add_rule('standard.ccccc', path_type=str)
        confp.add_rule('duplicates', path_type=dict)
        confp.add_rule('duplicates.*', path_type=dict)
        confp.add_rule('duplicates.*.aaaaa', path_type=str)
        confp.add_rule('duplicates.*.bbbbb', path_type=str)
        confp.add_rule('duplicates.*.ccccc', path_type=str)
        confp.add_rule('newstandard', path_type=dict)
        confp.add_rule('newstandard.*', path_type=dict)
        confp.add_rule('newstandard.*.aaaaa', path_type=str)
        confp.add_rule('newstandard.*.bbbbb', path_type=str)
        confp.add_rule('newstandard.*.ccccc', path_type=str)
        confp.add_rule('newstandard.*.xxxxx', path_type=str)

        self._write_file(self.conffile, """
        standard: &DEFAULT
          aaaaa: &as aaaaa
          bbbbb: &bs bbbbb
          ccccc: &cs ccccc
        duplicates:
          one: *DEFAULT
          two:
            <<: *DEFAULT
        newstandard:
          one:
            aaaaa: *as
            bbbbb: *bs
            ccccc: *cs
            xxxxx: *as
          two:
            <<: *DEFAULT
            aaaaa: *bs
            bbbbb: *as
            xxxxx: *cs
        """)

        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.standard.aaaaa, 'aaaaa')
        self.assertEqual(conf.standard.bbbbb, 'bbbbb')
        self.assertEqual(conf.standard.ccccc, 'ccccc')
        self.assertEqual(conf.duplicates.one.aaaaa, 'aaaaa')
        self.assertEqual(conf.duplicates.one.bbbbb, 'bbbbb')
        self.assertEqual(conf.duplicates.one.ccccc, 'ccccc')
        self.assertEqual(conf.duplicates.two.aaaaa, 'aaaaa')
        self.assertEqual(conf.duplicates.two.bbbbb, 'bbbbb')
        self.assertEqual(conf.duplicates.two.ccccc, 'ccccc')
        self.assertEqual(conf.newstandard.one.aaaaa, 'aaaaa')
        self.assertEqual(conf.newstandard.one.bbbbb, 'bbbbb')
        self.assertEqual(conf.newstandard.one.ccccc, 'ccccc')
        self.assertEqual(conf.newstandard.one.xxxxx, 'aaaaa')
        self.assertEqual(conf.newstandard.two.aaaaa, 'bbbbb')
        self.assertEqual(conf.newstandard.two.bbbbb, 'aaaaa')
        self.assertEqual(conf.newstandard.two.ccccc, 'ccccc')
        self.assertEqual(conf.newstandard.two.xxxxx, 'ccccc')

    def test_yaml_parsed_multiple_records_unsupported(self):
        """Test that multiple records raises an exception.

        The way the SafeLoader parser is invoked is expecting a single
        YAML document.  By replacing that parser, multiple records
        could probably be supported, but that extension would change
        current behavior.

        """
        confp = YamlConfigParser(path_type=list)
        confp.add_rule('*')

        self._write_file(self.conffile, """
        ---
        aaaaa
        ---
        bbbbb
        ---
        ccccc
        """)
        with self.assertRaisesRegex(ParseError, 'expected a single document'):
            confp.parse_file(self.conffile)


class ConfigRecordChecks(TestCase):
    """Test support for config records rather than files."""

    def test_config_record_map_good(self):
        """A config record with a map-like structure should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb')
        confrec = {'aaa': 'aaaaa', 'bbb': 'bbbbb'}
        conf = confp.parse_record(confrec, filename='*in-memory*')
        self.assertEqual(conf.aaa, 'aaaaa')
        self.assertEqual(conf.bbb, 'bbbbb')

    def test_config_record_map_bad(self):
        """A config record must specify a filename or identifying string."""
        confp = YamlConfigParser()
        confp.add_rule('field')
        confrec = {'field': 'aaaaa'}
        with self.assertRaisesRegex(ParseError, 'filename is missing'):
            _ = confp.parse_record(confrec, filename=None)


class ConfigFileChecks(TestCase):
    """Test correctly and incorrectly formatted and used config files."""

    def test_config_file_empty_bad(self):
        """An empty config file should be rejected."""
        confp = YamlConfigParser()
        confp.add_rule('field')
        self._test_conf_bad(confp, '', 'config cannot be empty or null')

    def test_config_file_string_bad_1(self):
        """An config file that just contains a string should be rejected."""
        confp = YamlConfigParser()
        confp.add_rule('field')
        self._test_conf_bad(
            confp=confp,
            conftext='aaaaa',
            excrex=r'config is a\(n\) str but a record or list is expected')

    def test_config_file_string_bad_2(self):
        """An config file that just contains a string should be rejected."""
        confp = YamlConfigParser()
        confp.add_rule('field')
        self._test_conf_bad(
            confp=confp,
            conftext='42',
            excrex=r'config is a\(n\) int but a record or list is expected')

    def test_config_file_map_good(self):
        """A config file with a map-like structure should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb')
        conf = self._test_conf_good(confp, """
        !!map
        aaa: aaaaa
        bbb: bbbbb
        """)
        self.assertIsInstance(conf, YamlConfig)
        self.assertEqual(conf.aaa, 'aaaaa')
        self.assertEqual(conf.bbb, 'bbbbb')

    def test_config_file_nullmap_good(self):
        """A config file with null complex map structure should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb')
        conf = self._test_conf_good(confp, """
        ? aaa
        ? bbb
        """)
        self.assertIsInstance(conf, YamlConfig)
        self.assertIsNone(conf.aaa)
        self.assertIsNone(conf.bbb)

    def test_config_file_list_good(self):
        """A config file with a list-like structure should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1')
        conf = self._test_conf_good(confp, """
        - aaaaa
        - bbbbb
        """)
        self.assertIsInstance(conf, YamlConfigList)
        self.assertEqual(conf[0], 'aaaaa')
        self.assertEqual(conf[1], 'bbbbb')

    def test_config_file_seq_good(self):
        """A config file with a seq tag should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1')
        conf = self._test_conf_good(confp, """
        !!seq
        - aaaaa
        - bbbbb
        """)
        self.assertIsInstance(conf, YamlConfigList)
        self.assertEqual(conf[0], 'aaaaa')
        self.assertEqual(conf[1], 'bbbbb')

    def test_config_file_pairs_good(self):
        """A config file with a pairs tag should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('0', nofollow=True)
        confp.add_rule('1', nofollow=True)
        conf = self._test_conf_good(confp, """
        !!pairs
        - aaa: aaaaa
        - bbb: bbbbb
        """)
        self.assertIsInstance(conf, YamlConfigList)
        self.assertEqual(conf[0][0], 'aaa')
        self.assertEqual(conf[0][1], 'aaaaa')
        self.assertEqual(conf[1][0], 'bbb')
        self.assertEqual(conf[1][1], 'bbbbb')

    def test_config_file_omap_good(self):
        """A config file with an omap tag should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('0', nofollow=True)
        confp.add_rule('1', nofollow=True)
        conf = self._test_conf_good(confp, """
        !!omap
        - aaa: aaaaa
        - bbb: bbbbb
        """)
        self.assertIsInstance(conf, YamlConfigList)
        self.assertEqual(conf[0][0], 'aaa')
        self.assertEqual(conf[0][1], 'aaaaa')
        self.assertEqual(conf[1][0], 'bbb')
        self.assertEqual(conf[1][1], 'bbbbb')

    def test_config_file_set_good(self):
        """A config file with a set tag should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1')
        conf = self._test_conf_good(confp, """
        !!set
        ? aaa
        ? bbb
        """)
        self.assertIsInstance(conf, YamlConfigList)
        self.assertSetEqual({conf[idx] for idx in conf}, {'aaa', 'bbb'})


class FieldNameChecks(TestCase):
    """Test limits of correct field-names rule matching and accessing."""

    def test_field_name_with_spaces_good(self):
        """Test that field names can contain spaces."""
        confp = YamlConfigParser()
        confp.add_rule('a field with a space')
        conf = self._test_conf_good(confp, 'a field with a space: aaaaa')
        self.assertListEqual(list(conf), ['a field with a space'])
        self.assertEqual(conf['a field with a space'], 'aaaaa')

    def test_field_name_with_leading_spaces_good(self):
        """Test that quoted field names can contain spaces."""
        confp = YamlConfigParser()
        confp.add_rule('  leading space field  ')
        conf = self._test_conf_good(confp, "'  leading space field  ': aaaaa")
        self.assertListEqual(list(conf), ['  leading space field  '])
        self.assertEqual(conf['  leading space field  '], 'aaaaa')

    def test_field_name_with_tabs_good(self):
        """Test that quoted field names can contain tabs."""
        confp = YamlConfigParser()
        confp.add_rule('field\twith\ttabs')
        conf = self._test_conf_good(confp, "'field\twith\ttabs': aaaaa")
        self.assertListEqual(list(conf), ['field\twith\ttabs'])
        self.assertEqual(conf['field\twith\ttabs'], 'aaaaa')

    def test_field_name_with_quoted_number_good(self):
        """Test that quoted field names can contain integers as strings."""
        confp = YamlConfigParser()
        confp.add_rule('42')
        conf = self._test_conf_good(confp, "'42': aaaaa")
        self.assertListEqual(list(conf), ['42'])
        self.assertEqual(conf['42'], 'aaaaa')

    def test_field_name_with_dash_good(self):
        """Test that a dash and colon is a map field not a list item."""
        confp = YamlConfigParser()
        confp.add_rule('-')
        conf = self._test_conf_good(confp, "-: aaaaa")
        self.assertIsInstance(conf, YamlConfig)
        self.assertListEqual(list(conf), ['-'])
        self.assertEqual(conf['-'], 'aaaaa')

    def test_field_name_with_colons_good(self):
        """Test that quoted field names can contain colons."""
        confp = YamlConfigParser()
        confp.add_rule('field:with:colons:')
        conf = self._test_conf_good(confp, '"field:with:colons:": aaaaa')
        self.assertListEqual(list(conf), ['field:with:colons:'])
        self.assertEqual(conf['field:with:colons:'], 'aaaaa')

    def test_field_name_with_asterisks_okay(self):
        """Test field names with asterisks are okay if wildcard matched."""
        confp = YamlConfigParser()
        confp.add_rule('*')
        conf = self._test_conf_good(confp, """
        a*field: aaaaa
        '*another*field*': bbbbb
        "*": ccccc
        """)
        self.assertSetEqual(set(conf), {'a*field', '*another*field*', '*'})
        self.assertEqual(conf['a*field'], 'aaaaa')
        self.assertEqual(conf['*another*field*'], 'bbbbb')
        self.assertEqual(conf['*'], 'ccccc')

    def test_field_name_with_dots_okay(self):
        """Test field names with dots are okay if wildcard matched."""
        confp = YamlConfigParser()
        confp.add_rule('*')
        conf = self._test_conf_good(confp, """
        a.field: aaaaa
        '.another.field.': bbbbb
        ".": ccccc
        """)
        self.assertSetEqual(set(conf), {'a.field', '.another.field.', '.'})
        self.assertEqual(conf['a.field'], 'aaaaa')
        self.assertEqual(conf['.another.field.'], 'bbbbb')
        self.assertEqual(conf['.'], 'ccccc')

    def test_field_name_with_leading_underscores_warning(self):
        """Test that field names with leading underscores generate warning."""
        confp = YamlConfigParser()
        confp.add_rule('_the_field_')

        self._write_file(self.conffile, """
        _the_field_: aaaaa
        """)

        # Run without warnings for correctness
        warning_off_orig = print_underscore_warning.off
        print_underscore_warning.off = True
        try:
            with CaptureIO('{0}_nowarn'.format(self.testname)) as capio:
                conf = confp.parse_file(self.conffile)
            stderr = capio.get_stderr()
            self.assertEqual(stderr, '')
        finally:
            print_underscore_warning.off = warning_off_orig

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
        self.assertListEqual(list(conf), ['_the_field_'])
        self.assertEqual(conf['_the_field_'], 'aaaaa')

    def test_field_name_negative_list_index_good_1(self):
        """Test negative list index for access."""
        confp = YamlConfigParser()
        confp.add_rule('*')
        conf = self._test_conf_good(confp, """
        - aaaaa
        - bbbbb
        - ccccc
        - ddddd
        - eeeee
        """)
        self.assertEqual(conf[-1], 'eeeee')
        self.assertEqual(conf[-2], 'ddddd')

    def test_field_name_negative_list_index_good_2(self):
        """Test string representing negative list index for access."""
        confp = YamlConfigParser()
        confp.add_rule('*')
        conf = self._test_conf_good(confp, """
        - aaaaa
        - bbbbb
        - ccccc
        - ddddd
        - eeeee
        """)
        self.assertEqual(conf['-1'], 'eeeee')
        self.assertEqual(conf['-2'], 'ddddd')

    def test_field_name_float_list_index_good(self):
        """Test float representing list index for access get truncated."""
        confp = YamlConfigParser()
        confp.add_rule('*')
        conf = self._test_conf_good(confp, """
        - aaaaa
        - bbbbb
        - ccccc
        - ddddd
        - eeeee
        """)
        self.assertEqual(conf[1.0], 'bbbbb')
        self.assertEqual(conf[1.9], 'bbbbb')
        self.assertEqual(conf[-2.0], 'ddddd')
        self.assertEqual(conf[-2.9], 'ddddd')

    def test_field_name_float_list_index_bad(self):
        """Test decimal-number float representing list index for access."""
        confp = YamlConfigParser()
        confp.add_rule('*')
        conf = self._test_conf_good(confp, """
        - aaaaa
        - bbbbb
        - ccccc
        - ddddd
        - eeeee
        """)
        _ = conf[1.5]

    def test_field_name_list_slice_index_bad(self):
        """Test that list slice raises error."""
        confp = YamlConfigParser()
        confp.add_rule('*')
        conf = self._test_conf_good(confp, """
        - aaaaa
        - bbbbb
        - ccccc
        - ddddd
        - eeeee
        """)
        with self.assertRaisesRegex(
                KeyError, 'slice.* is not an integer list index'):
            _ = conf[1::2]

    def test_field_name_list_non_int_bad(self):
        """Test that non-integer string for list index raises error."""
        confp = YamlConfigParser()
        confp.add_rule('*')
        conf = self._test_conf_good(confp, """
        - aaaaa
        - bbbbb
        - ccccc
        - ddddd
        - eeeee
        """)
        with self.assertRaisesRegex(
                KeyError, '"aaa" is not an integer list index'):
            _ = conf['aaa']

    def test_field_name_list_index_contains_good(self):
        """Test list index contains behavior."""
        confp = YamlConfigParser()
        confp.add_rule('*')
        conf = self._test_conf_good(confp, """
        - aaaaa
        - bbbbb
        - ccccc
        - ddddd
        - eeeee
        """)
        self.assertIn(2, conf)
        self.assertIn('2', conf)
        self.assertIn(2.0, conf)
        self.assertIn(2.5, conf)
        self.assertIn(-0.5, conf)
        self.assertNotIn(-2, conf)
        self.assertNotIn('-2', conf)
        self.assertNotIn(-2.5, conf)
        self.assertNotIn('two', conf)


class RulePathChecks(TestCase):
    """Test that rules ensuring path presence/absence are enforced."""

    def test_rule_path_root_map_empty_good(self):
        """An empty ruleset should accept an empty map config file."""
        confp = YamlConfigParser()
        conf = self._test_conf_good(confp, '{}')
        self.assertIsInstance(conf, YamlConfig)
        self.assertEqual(len(conf), 0)

    def test_rule_path_root_map_fields_good(self):
        """Specifying root-level fields should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb')
        confp.add_rule('ccc')
        conf = self._test_conf_good(confp, """
        aaa: aaaaa
        bbb: bbbbb
        ccc: ccccc
        """)
        self.assertIsInstance(conf, YamlConfig)
        self.assertListEqual(list(conf), ['aaa', 'bbb', 'ccc'])
        self.assertEqual(conf.aaa, 'aaaaa')
        self.assertEqual(conf.bbb, 'bbbbb')
        self.assertEqual(conf.ccc, 'ccccc')

    def test_rule_path_root_map_missing_field_bad_1(self):
        """Missing root-level fields should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb')
        confp.add_rule('ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            bbb: bbbbb
            ccc: ccccc
            """,
            excrex='"aaa" is missing')

    def test_rule_path_root_map_missing_field_bad_2(self):
        """Missing root-level fields should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb')
        confp.add_rule('ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa: aaaaa
            ccc: ccccc
            """,
            excrex='"bbb" is missing')

    def test_rule_path_root_map_missing_field_bad_3(self):
        """Missing root-level fields should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb')
        confp.add_rule('ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa: aaaaa
            bbb: bbbbb
            """,
            excrex='"ccc" is missing')

    def test_rule_path_root_map_missing_field_bad_4(self):
        """Missing root-level fields should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb')
        confp.add_rule('ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            ccc: ccccc
            """,
            excrex='"aaa" is missing')

    def test_rule_path_root_map_missing_field_bad_5(self):
        """Missing root-level fields should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb')
        confp.add_rule('ccc')
        self._test_conf_bad(
            confp=confp,
            conftext='{}',
            excrex='"aaa" is missing')

    def test_rule_path_root_map_extra_field_bad_1(self):
        """Unexpected root-level fields should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb')
        confp.add_rule('ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            xxx: xxxxx
            aaa: aaaaa
            bbb: bbbbb
            ccc: ccccc
            """,
            excrex='"xxx" unexpected by parser')

    def test_rule_path_root_map_extra_field_bad_2(self):
        """Unexpected root-level fields should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb')
        confp.add_rule('ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa: aaaaa
            xxx: xxxxx
            bbb: bbbbb
            ccc: ccccc
            """,
            excrex='"xxx" unexpected by parser')

    def test_rule_path_root_map_extra_field_bad_3(self):
        """Unexpected root-level fields should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb')
        confp.add_rule('ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa: aaaaa
            bbb: bbbbb
            xxx: xxxxx
            ccc: ccccc
            """,
            excrex='"xxx" unexpected by parser')

    def test_rule_path_root_map_extra_field_bad_4(self):
        """Unexpected root-level fields should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb')
        confp.add_rule('ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa: aaaaa
            bbb: bbbbb
            ccc: ccccc
            xxx: xxxxx
            """,
            excrex='"xxx" unexpected by parser')

    def test_rule_path_root_map_extra_field_bad_5(self):
        """Unexpected root-level fields should be detected."""
        confp = YamlConfigParser()
        self._test_conf_bad(
            confp=confp,
            conftext='xxx: xxxxx',
            excrex='"xxx" unexpected by parser')

    def test_rule_path_root_map_missing_and_extra_fields_bad(self):
        """A missing field should be detected before an extra field."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb')
        confp.add_rule('ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa: aaaaa
            bbb: bbbbb
            xxx: xxxxx
            """,
            excrex='"ccc" is missing')

    def test_rule_path_root_list_empty_good(self):
        """An empty ruleset should accept an empty list config file."""
        confp = YamlConfigParser()
        conf = self._test_conf_good(confp, '[]')
        self.assertIsInstance(conf, YamlConfigList)
        self.assertEqual(len(conf), 0)

    def test_rule_path_root_list_fields_good(self):
        """Specifying root-level fields should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1')
        confp.add_rule('2')
        conf = self._test_conf_good(confp, """
        - aaaaa
        - bbbbb
        - ccccc
        """)
        self.assertIsInstance(conf, YamlConfigList)
        self.assertListEqual(list(conf), ['0', '1', '2'])
        self.assertEqual(conf[0], 'aaaaa')
        self.assertEqual(conf[1], 'bbbbb')
        self.assertEqual(conf[2], 'ccccc')

    def test_rule_path_root_list_missing_field_bad_1(self):
        """Missing root-level fields should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1')
        confp.add_rule('2')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            - aaaaa
            - bbbbb
            """,
            excrex='"2" is missing')

    def test_rule_path_root_list_missing_field_bad_2(self):
        """Missing root-level fields should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1')
        confp.add_rule('2')
        self._test_conf_bad(
            confp=confp,
            conftext='- aaaaa',
            excrex='"1" is missing')

    def test_rule_path_root_list_missing_field_bad_3(self):
        """Missing root-level fields should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1')
        confp.add_rule('2')
        self._test_conf_bad(
            confp=confp,
            conftext='[]',
            excrex='"0" is missing')

    def test_rule_path_root_list_extra_field_bad_1(self):
        """Unexpected root-level fields should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1')
        confp.add_rule('2')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            - aaaaa
            - bbbbb
            - ccccc
            - xxxxx
            """,
            excrex='"3" unexpected by parser')

    def test_rule_path_root_list_extra_field_bad_2(self):
        """Unexpected root-level fields should be detected."""
        confp = YamlConfigParser()
        self._test_conf_bad(
            confp=confp,
            conftext='- xxxxx',
            excrex='"0" unexpected by parser')

    def test_rule_path_root_list_rule_index_gap_bad(self):
        """Gap in root rule indexes should raise error."""
        confp = YamlConfigParser()
        confp.add_rule('1')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            - aaaaa
            """,
            excrex='"1" is missing')

    def test_rule_path_nested_map_empty_good(self):
        """A nested map with no subrules should accept an empty map."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa')
        conf = self._test_conf_good(confp, """
        aaa:
          aaa: {}
        """)
        self.assertIsInstance(conf.aaa.aaa, YamlConfig)
        self.assertEqual(len(conf.aaa.aaa), 0)

    def test_rule_path_nested_map_null_leaf_bad(self):
        """A nested map with a null instead of a leaf should be rejected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.aaa.bbb')
        confp.add_rule('aaa.aaa.ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
            """,
            excrex='"aaa.aaa" is .* but a record or list is expected')

    def test_rule_path_nested_map_leaf_fields_good(self):
        """Specifying nested map with subrules should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.aaa.bbb')
        confp.add_rule('aaa.aaa.ccc')
        conf = self._test_conf_good(confp, """
        aaa:
          aaa:
            aaa: aaaaa
            bbb: bbbbb
            ccc: ccccc
        """)
        self.assertIsInstance(conf.aaa.aaa, YamlConfig)
        self.assertListEqual(list(conf.aaa.aaa), ['aaa', 'bbb', 'ccc'])
        self.assertEqual(conf.aaa.aaa.aaa, 'aaaaa')
        self.assertEqual(conf.aaa.aaa.bbb, 'bbbbb')
        self.assertEqual(conf.aaa.aaa.ccc, 'ccccc')

    def test_rule_path_nested_map_missing_leaf_field_bad_1(self):
        """Missing field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.aaa.bbb')
        confp.add_rule('aaa.aaa.ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                bbb: bbbbb
                ccc: ccccc
            """,
            excrex='"aaa.aaa.aaa" is missing')

    def test_rule_path_nested_map_missing_leaf_field_bad_2(self):
        """Missing field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.aaa.bbb')
        confp.add_rule('aaa.aaa.ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                aaa: aaaaa
                ccc: ccccc
            """,
            excrex='"aaa.aaa.bbb" is missing')

    def test_rule_path_nested_map_missing_leaf_field_bad_3(self):
        """Missing field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.aaa.bbb')
        confp.add_rule('aaa.aaa.ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                aaa: aaaaa
                bbb: bbbbb
            """,
            excrex='"aaa.aaa.ccc" is missing')

    def test_rule_path_nested_map_missing_leaf_field_bad_4(self):
        """Missing field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.aaa.bbb')
        confp.add_rule('aaa.aaa.ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                ccc: ccccc
            """,
            excrex='"aaa.aaa.aaa" is missing')

    def test_rule_path_nested_map_missing_leaf_field_bad_5(self):
        """Missing field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.aaa.bbb')
        confp.add_rule('aaa.aaa.ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa: {}
            """,
            excrex='"aaa.aaa.aaa" is missing')

    def test_rule_path_nested_map_extra_leaf_field_bad_1(self):
        """Unexpected field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.aaa.bbb')
        confp.add_rule('aaa.aaa.ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                xxx: xxxxx
                aaa: aaaaa
                bbb: bbbbb
                ccc: ccccc
            """,
            excrex='"aaa.aaa.xxx" unexpected by parser')

    def test_rule_path_nested_map_extra_leaf_field_bad_2(self):
        """Unexpected field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.aaa.bbb')
        confp.add_rule('aaa.aaa.ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                aaa: aaaaa
                xxx: xxxxx
                bbb: bbbbb
                ccc: ccccc
            """,
            excrex='"aaa.aaa.xxx" unexpected by parser')

    def test_rule_path_nested_map_extra_leaf_field_bad_3(self):
        """Unexpected field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.aaa.bbb')
        confp.add_rule('aaa.aaa.ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                aaa: aaaaa
                bbb: bbbbb
                xxx: xxxxx
                ccc: ccccc
            """,
            excrex='"aaa.aaa.xxx" unexpected by parser')

    def test_rule_path_nested_map_extra_leaf_field_bad_4(self):
        """Unexpected field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.aaa.bbb')
        confp.add_rule('aaa.aaa.ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                aaa: aaaaa
                bbb: bbbbb
                ccc: ccccc
                xxx: xxxxx
            """,
            excrex='"aaa.aaa.xxx" unexpected by parser')

    def test_rule_path_nested_map_extra_leaf_field_bad_5(self):
        """Unexpected field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                xxx: xxxxx
            """,
            excrex='"aaa.aaa.xxx" unexpected by parser')

    def test_rule_path_nested_map_missing_and_extra_leaf_fields_bad(self):
        """A missing field should be detected before an extra field."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.aaa.bbb')
        confp.add_rule('aaa.aaa.ccc')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                xxx: xxxxx
                aaa: aaaaa
                bbb: bbbbb
            """,
            excrex='"aaa.aaa.ccc" is missing')

    def test_rule_path_nested_map_null_path_bad(self):
        """A nested map with a null along the path should be rejected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.aaa.bbb')
        confp.add_rule('aaa.aaa.ccc')
        self._test_conf_bad(
            confp=confp,
            conftext='aaa:',
            excrex='"aaa" is .* but a record or list is expected')

    def test_rule_path_nested_map_path_fields_good(self):
        """Specifying nested map with subrules should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.bbb.aaa')
        confp.add_rule('aaa.ccc.aaa')
        conf = self._test_conf_good(confp, """
        aaa:
          aaa:
            aaa: aaaaa
          bbb:
            aaa: bbbbb
          ccc:
            aaa: ccccc
        """)
        self.assertIsInstance(conf.aaa, YamlConfig)
        self.assertListEqual(list(conf.aaa), ['aaa', 'bbb', 'ccc'])
        self.assertEqual(conf.aaa.aaa.aaa, 'aaaaa')
        self.assertEqual(conf.aaa.bbb.aaa, 'bbbbb')
        self.assertEqual(conf.aaa.ccc.aaa, 'ccccc')

    def test_rule_path_nested_map_missing_path_field_bad_1(self):
        """Missing field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.bbb.aaa')
        confp.add_rule('aaa.ccc.aaa')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              bbb:
                aaa: bbbbb
              ccc:
                aaa: ccccc
            """,
            excrex='"aaa.aaa" is missing')

    def test_rule_path_nested_map_missing_path_field_bad_2(self):
        """Missing field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.bbb.aaa')
        confp.add_rule('aaa.ccc.aaa')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                aaa: aaaaa
              ccc:
                aaa: ccccc
            """,
            excrex='"aaa.bbb" is missing')

    def test_rule_path_nested_map_missing_path_field_bad_3(self):
        """Missing field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.bbb.aaa')
        confp.add_rule('aaa.ccc.aaa')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                aaa: aaaaa
              bbb:
                aaa: bbbbb
            """,
            excrex='"aaa.ccc" is missing')

    def test_rule_path_nested_map_missing_path_field_bad_4(self):
        """Missing field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.bbb.aaa')
        confp.add_rule('aaa.ccc.aaa')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              ccc:
                aaa: ccccc
            """,
            excrex='"aaa.aaa" is missing')

    def test_rule_path_nested_map_missing_path_field_bad_5(self):
        """Missing field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.bbb.aaa')
        confp.add_rule('aaa.ccc.aaa')
        self._test_conf_bad(
            confp=confp,
            conftext='aaa: {}',
            excrex='"aaa.aaa" is missing')

    def test_rule_path_nested_map_extra_path_field_bad_1(self):
        """Missing field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.bbb.aaa')
        confp.add_rule('aaa.ccc.aaa')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              xxx:
                aaa: xxxxx
              aaa:
                aaa: aaaaa
              bbb:
                aaa: bbbbb
              ccc:
                aaa: ccccc
            """,
            excrex='"aaa.xxx" unexpected by parser')

    def test_rule_path_nested_map_extra_path_field_bad_2(self):
        """Missing field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.bbb.aaa')
        confp.add_rule('aaa.ccc.aaa')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                aaa: aaaaa
              xxx:
                aaa: xxxxx
              bbb:
                aaa: bbbbb
              ccc:
                aaa: ccccc
            """,
            excrex='"aaa.xxx" unexpected by parser')

    def test_rule_path_nested_map_extra_path_field_bad_3(self):
        """Missing field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.bbb.aaa')
        confp.add_rule('aaa.ccc.aaa')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                aaa: aaaaa
              bbb:
                aaa: bbbbb
              xxx:
                aaa: xxxxx
              ccc:
                aaa: ccccc
            """,
            excrex='"aaa.xxx" unexpected by parser')

    def test_rule_path_nested_map_extra_path_field_bad_4(self):
        """Missing field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.bbb.aaa')
        confp.add_rule('aaa.ccc.aaa')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                aaa: aaaaa
              bbb:
                aaa: bbbbb
              ccc:
                aaa: ccccc
              xxx:
                aaa: xxxxx
            """,
            excrex='"aaa.xxx" unexpected by parser')

    def test_rule_path_nested_map_extra_path_field_bad_5(self):
        """Missing field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              xxx:
                aaa: xxxxx
            """,
            excrex='"aaa.xxx" unexpected by parser')

    def test_rule_path_nested_map_missing_and_extra_path_fields_bad(self):
        """Missing field in nested map should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.aaa')
        confp.add_rule('aaa.bbb.aaa')
        confp.add_rule('aaa.ccc.aaa')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              xxx:
                aaa: xxxxx
              bbb:
                aaa: bbbbb
              ccc:
                aaa: ccccc
            """,
            excrex='"aaa.aaa" is missing')

    def test_rule_path_nested_list_empty_good(self):
        """A nested list with no subrules should accept an empty list."""
        confp = YamlConfigParser()
        confp.add_rule('0.0')
        conf = self._test_conf_good(confp, """
        -
          - []
        """)
        self.assertIsInstance(conf[0][0], YamlConfigList)
        self.assertEqual(len(conf[0][0]), 0)

    def test_rule_path_nested_list_null_leaf_bad(self):
        """A nested list with a null instead of a leaf should be rejected."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0')
        confp.add_rule('0.0.1')
        confp.add_rule('0.0.2')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            -
              -
            """,
            excrex='"0.0" is .* but a record or list is expected')

    def test_rule_path_nested_list_leaf_fields_good(self):
        """Specifying nested list with subrules should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0')
        confp.add_rule('0.0.1')
        confp.add_rule('0.0.2')
        conf = self._test_conf_good(confp, """
        -
          -
            - aaaaa
            - bbbbb
            - ccccc
        """)
        self.assertIsInstance(conf[0][0], YamlConfigList)
        self.assertListEqual(list(conf[0][0]), ['0', '1', '2'])
        self.assertEqual(conf[0][0][0], 'aaaaa')
        self.assertEqual(conf[0][0][1], 'bbbbb')
        self.assertEqual(conf[0][0][2], 'ccccc')

    def test_rule_path_nested_list_missing_leaf_field_bad_1(self):
        """Missing field in nested list should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0')
        confp.add_rule('0.0.1')
        confp.add_rule('0.0.2')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            -
              -
                - aaaaa
                - bbbbb
            """,
            excrex='"0.0.2" is missing')

    def test_rule_path_nested_list_missing_leaf_field_bad_2(self):
        """Missing field in nested list should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0')
        confp.add_rule('0.0.1')
        confp.add_rule('0.0.2')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            -
              -
                - aaaaa
            """,
            excrex='"0.0.1" is missing')

    def test_rule_path_nested_list_missing_leaf_field_bad_3(self):
        """Missing field in nested list should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0')
        confp.add_rule('0.0.1')
        confp.add_rule('0.0.2')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            -
              - []
            """,
            excrex='"0.0.0" is missing')

    def test_rule_path_nested_list_extra_leaf_field_bad_1(self):
        """Unexpected field in nested list should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0')
        confp.add_rule('0.0.1')
        confp.add_rule('0.0.2')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            -
              -
                - aaaaa
                - bbbbb
                - ccccc
                - xxxxx
            """,
            excrex='"0.0.3" unexpected by parser')

    def test_rule_path_nested_list_extra_leaf_field_bad_2(self):
        """Unexpected field in nested list should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('0.0')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            -
              -
                - xxxxx
            """,
            excrex='"0.0.0" unexpected by parser')

    def test_rule_path_nested_list_null_path_bad(self):
        """A nested list with a null along the path should be rejected."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0')
        confp.add_rule('0.0.1')
        confp.add_rule('0.0.2')
        self._test_conf_bad(
            confp=confp,
            conftext='-',
            excrex='"0" is .* but a record or list is expected')

    def test_rule_path_nested_list_path_fields_good(self):
        """Specifying nested list with subrules should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0')
        confp.add_rule('0.1.0')
        confp.add_rule('0.2.0')
        conf = self._test_conf_good(confp, """
        -
          -
            - aaaaa
          -
            - bbbbb
          -
            - ccccc
        """)
        self.assertIsInstance(conf[0], YamlConfigList)
        self.assertListEqual(list(conf[0]), ['0', '1', '2'])
        self.assertEqual(conf[0][0][0], 'aaaaa')
        self.assertEqual(conf[0][1][0], 'bbbbb')
        self.assertEqual(conf[0][2][0], 'ccccc')

    def test_rule_path_nested_list_missing_path_field_bad_1(self):
        """Missing field in nested list should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0')
        confp.add_rule('0.1.0')
        confp.add_rule('0.2.0')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            -
              -
                - aaaaa
              -
                - bbbbb
            """,
            excrex='"0.2" is missing')

    def test_rule_path_nested_list_missing_path_field_bad_2(self):
        """Missing field in nested list should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0')
        confp.add_rule('0.1.0')
        confp.add_rule('0.2.0')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            -
              -
                - aaaaa
            """,
            excrex='"0.1" is missing')

    def test_rule_path_nested_list_missing_path_field_bad_3(self):
        """Missing field in nested list should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0')
        confp.add_rule('0.1.0')
        confp.add_rule('0.2.0')
        self._test_conf_bad(
            confp=confp,
            conftext='- []',
            excrex='"0.0" is missing')

    def test_rule_path_nested_list_extra_path_field_bad_1(self):
        """Missing field in nested list should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0')
        confp.add_rule('0.1.0')
        confp.add_rule('0.2.0')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            -
              -
                - aaaaa
              -
                - bbbbb
              -
                - ccccc
              -
                - xxxxx
            """,
            excrex='"0.3" unexpected by parser')

    def test_rule_path_nested_list_extra_path_field_bad_2(self):
        """Missing field in nested list should be detected."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            -
              -
                - xxxxx
            """,
            excrex='"0.0" unexpected by parser')


class RulePathWildcardChecks(TestCase):
    """Test that rules involving wildcards work as expected."""

    def test_wildcard_root_map_single_field_good(self):
        """Test wildcard on root map accepts single field."""
        confp = YamlConfigParser()
        confp.add_rule('*')
        conf = self._test_conf_good(confp, 'aaa: aaaaa')
        self.assertSetEqual(set(conf), {'aaa'})
        self.assertEqual(conf.aaa, 'aaaaa')

    def test_wildcard_root_map_many_fields_good(self):
        """Test wildcard on root map accepts many fields."""
        confp = YamlConfigParser()
        confp.add_rule('*')
        conf = self._test_conf_good(confp, """
        aaa: aaaaa
        bbb: bbbbb
        ccc: ccccc
        ddd: ddddd
        eee: eeeee
        fff: fffff
        """)
        self.assertSetEqual(
            set(conf), {'aaa', 'bbb', 'ccc', 'ddd', 'eee', 'fff'})
        self.assertEqual(conf.aaa, 'aaaaa')
        self.assertEqual(conf.bbb, 'bbbbb')
        self.assertEqual(conf.ccc, 'ccccc')
        self.assertEqual(conf.ddd, 'ddddd')
        self.assertEqual(conf.eee, 'eeeee')
        self.assertEqual(conf.fff, 'fffff')

    def test_wildcard_root_map_no_fields_bad(self):
        """Test wildcard on root map raises error on no fields."""
        confp = YamlConfigParser()
        confp.add_rule('*')
        self._test_conf_bad(
            confp=confp,
            conftext='{}',
            excrex=r'\*root\* must contain at least one field')

    def test_wildcard_root_list_single_field_good(self):
        """Test wildcard on root list accepts single field."""
        confp = YamlConfigParser()
        confp.add_rule('*')
        conf = self._test_conf_good(confp, '- aaaaa')
        self.assertListEqual(list(conf), ['0'])
        self.assertEqual(conf[0], 'aaaaa')

    def test_wildcard_root_list_many_fields_good(self):
        """Test wildcard on root list accepts many fields."""
        confp = YamlConfigParser()
        confp.add_rule('*')
        conf = self._test_conf_good(confp, """
        - aaaaa
        - bbbbb
        - ccccc
        - ddddd
        - eeeee
        - fffff
        """)
        self.assertListEqual(list(conf), ['0', '1', '2', '3', '4', '5'])
        self.assertEqual(conf[0], 'aaaaa')
        self.assertEqual(conf[1], 'bbbbb')
        self.assertEqual(conf[2], 'ccccc')
        self.assertEqual(conf[3], 'ddddd')
        self.assertEqual(conf[4], 'eeeee')
        self.assertEqual(conf[5], 'fffff')

    def test_wildcard_root_list_no_fields_bad(self):
        """Test wildcard on root list raises error on no fields."""
        confp = YamlConfigParser()
        confp.add_rule('*')
        self._test_conf_bad(
            confp=confp,
            conftext='[]',
            excrex=r'\*root\* must contain at least one field')

    def test_wildcard_map_leaf_single_field_good(self):
        """Test wildcard on map leaf should accepts single field."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.*')
        conf = self._test_conf_good(confp, """
        aaa:
          aaa:
            aaa: aaaaa
        """)
        self.assertSetEqual(set(conf.aaa.aaa), {'aaa'})
        self.assertEqual(conf.aaa.aaa.aaa, 'aaaaa')

    def test_wildcard_map_leaf_many_fields_good(self):
        """Test wildcard on map leaf accepts many fields."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.*')
        conf = self._test_conf_good(confp, """
        aaa:
          aaa:
            aaa: aaaaa
            bbb: bbbbb
            ccc: ccccc
            ddd: ddddd
            eee: eeeee
            fff: fffff
        """)
        self.assertSetEqual(
            set(conf.aaa.aaa), {'aaa', 'bbb', 'ccc', 'ddd', 'eee', 'fff'})
        self.assertEqual(conf.aaa.aaa.aaa, 'aaaaa')
        self.assertEqual(conf.aaa.aaa.bbb, 'bbbbb')
        self.assertEqual(conf.aaa.aaa.ccc, 'ccccc')
        self.assertEqual(conf.aaa.aaa.ddd, 'ddddd')
        self.assertEqual(conf.aaa.aaa.eee, 'eeeee')
        self.assertEqual(conf.aaa.aaa.fff, 'fffff')

    def test_wildcard_map_leaf_no_fields_bad(self):
        """Test wildcard on map leaf raises error on no fields."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.*')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa: {}
            """,
            excrex='"aaa.aaa" must contain at least one field')

    def test_wildcard_list_leaf_single_field_good(self):
        """Test wildcard on list leaf accepts single field."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.*')
        conf = self._test_conf_good(confp, """
        -
          -
            - aaaaa
        """)
        self.assertListEqual(list(conf[0][0]), ['0'])
        self.assertEqual(conf[0][0][0], 'aaaaa')

    def test_wildcard_list_leaf_many_fields_good(self):
        """Test wildcard on list leaf accepts many fields."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.*')
        conf = self._test_conf_good(confp, """
        -
          -
            - aaaaa
            - bbbbb
            - ccccc
            - ddddd
            - eeeee
            - fffff
        """)
        self.assertListEqual(list(conf[0][0]), ['0', '1', '2', '3', '4', '5'])
        self.assertEqual(conf[0][0][0], 'aaaaa')
        self.assertEqual(conf[0][0][1], 'bbbbb')
        self.assertEqual(conf[0][0][2], 'ccccc')
        self.assertEqual(conf[0][0][3], 'ddddd')
        self.assertEqual(conf[0][0][4], 'eeeee')
        self.assertEqual(conf[0][0][5], 'fffff')

    def test_wildcard_list_leaf_no_fields_bad(self):
        """Test wildcard on list leaf raise error on no fields."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.*')
        self._test_conf_bad(
            confp=confp,
            conftext='- - []',
            excrex='"0.0" must contain at least one field')

    def test_wildcard_sequences_match_depth_good(self):
        """Test wildcard sequences ensure consistent depth and little else."""
        confp = YamlConfigParser()
        confp.add_rule('*.*.*.*.*')
        conf = self._test_conf_good(confp, """
        # All leaves are five levels deep
        aaa:
        - aaa:
          - aaa: aaaaa
            bbb: bbbbb
          - aaa: ccccc
            bbb: ddddd
          bbb:
          - aaa: eeeee
        bbb:
          aaa:
            aaa:
              aaa:
                aaa: fffff
            bbb:
            - aaa: ggggg
            - aaa: hhhhh
        """)
        self.assertEqual(conf.aaa[0].aaa[0].aaa, 'aaaaa')
        self.assertEqual(conf.aaa[0].aaa[0].bbb, 'bbbbb')
        self.assertEqual(conf.aaa[0].aaa[1].aaa, 'ccccc')
        self.assertEqual(conf.aaa[0].aaa[1].bbb, 'ddddd')
        self.assertEqual(conf.aaa[0].bbb[0].aaa, 'eeeee')
        self.assertEqual(conf.bbb.aaa.aaa.aaa.aaa, 'fffff')
        self.assertEqual(conf.bbb.aaa.bbb[0].aaa, 'ggggg')
        self.assertEqual(conf.bbb.aaa.bbb[1].aaa, 'hhhhh')

    def test_wildcard_sequences_truncated_depth_bad(self):
        """Test wildcard sequences ensure consistent depth."""
        confp = YamlConfigParser()
        confp.add_rule('*.*.*.*.*')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                aaa:
                  aaa:
                    aaa: aaaaa
              bbb:             # <- missing depth
              ccc:
                aaa:
                  aaa:
                    aaa: bbbbbb
            """,
            excrex='"aaa.bbb" is .* but a record or list is expected')

    def test_wildcard_sequences_too_deep_bad(self):
        """Test Wildcard sequences ensure consistent depth."""
        confp = YamlConfigParser()
        confp.add_rule('*.*.*.*.*')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                aaa:
                  aaa:
                    aaa: aaaaa
              bbb:
                aaa:
                  aaa:
                    aaa:
                      aaa: bbbbbb   # <- too deep
              ccc:
                aaa:
                  aaa:
                    aaa: ccccc
            """,
            excrex='"aaa.bbb.aaa.aaa.aaa.aaa" unexpected by parser')

    def test_wildcard_fixed_mixed_structure_good(self):
        """Test wildcards mixed with fixed fields on path enforce structure.

        The logic of the mixed structure used in this and the other
        test_wildcard_fixed_mixed_structure_* tests is as follows:

        At the first and third levels:
          - TypeA: two levels down must have a TypeA and TypeB
          - TypeB: two levels down must have a TypeC
          - TypeC: two levels down must have a TypeC
        """
        confp = YamlConfigParser()
        confp.add_rule('TypeA.*.TypeA.*.TypeA.*', path_type=int)
        confp.add_rule('TypeA.*.TypeA.*.TypeB.*', path_type=int)
        confp.add_rule('TypeA.*.TypeB.*.TypeC.*', path_type=int)
        confp.add_rule('TypeB.*.TypeC.*.TypeC.*', path_type=int)

        conf = self._test_conf_good(confp, """
        TypeA:
          xxxxx:
            TypeA:
              xxxxx:
                TypeA:
                  xxxxx: 1
                  yyyyy: 2
                  zzzzz: 3
                TypeB:
                  xxxxx: 4
                  yyyyy: 5
              yyyyy:
                TypeA:
                  xxxxx: 6
                TypeB:
                  xxxxx: 7
            TypeB:
              xxxxx:
                TypeC:
                  xxxxx: 8
                  yyyyy: 9
              yyyyy:
                TypeC:
                  xxxxx: 10
        TypeB:
          xxxxx:
            TypeC:
              xxxxx:
                TypeC:
                  xxxxx: 11
              yyyyy:
                TypeC:
                  xxxxx: 12
              zzzzz:
                TypeC:
                  xxxxx: 13
          yyyyy:
            TypeC:
              xxxxx:
                TypeC:
                  xxxxx: 14
        """)
        self.assertEqual(conf.TypeA.xxxxx.TypeA.xxxxx.TypeA.xxxxx, 1)
        self.assertEqual(conf.TypeA.xxxxx.TypeA.xxxxx.TypeA.yyyyy, 2)
        self.assertEqual(conf.TypeA.xxxxx.TypeA.xxxxx.TypeA.zzzzz, 3)
        self.assertEqual(conf.TypeA.xxxxx.TypeA.xxxxx.TypeB.xxxxx, 4)
        self.assertEqual(conf.TypeA.xxxxx.TypeA.xxxxx.TypeB.yyyyy, 5)
        self.assertEqual(conf.TypeA.xxxxx.TypeA.yyyyy.TypeA.xxxxx, 6)
        self.assertEqual(conf.TypeA.xxxxx.TypeA.yyyyy.TypeB.xxxxx, 7)
        self.assertEqual(conf.TypeA.xxxxx.TypeB.xxxxx.TypeC.xxxxx, 8)
        self.assertEqual(conf.TypeA.xxxxx.TypeB.xxxxx.TypeC.yyyyy, 9)
        self.assertEqual(conf.TypeA.xxxxx.TypeB.yyyyy.TypeC.xxxxx, 10)
        self.assertEqual(conf.TypeB.xxxxx.TypeC.xxxxx.TypeC.xxxxx, 11)
        self.assertEqual(conf.TypeB.xxxxx.TypeC.yyyyy.TypeC.xxxxx, 12)
        self.assertEqual(conf.TypeB.xxxxx.TypeC.zzzzz.TypeC.xxxxx, 13)
        self.assertEqual(conf.TypeB.yyyyy.TypeC.xxxxx.TypeC.xxxxx, 14)

    def test_wildcard_fixed_mixed_structure_bad(self):
        """Test wildcards mixed with fixed fields on path enforce structure.

        In this test case, the parser should require that
        TypeA.xxxxx.TypeA.yyyyy contain a TypeA and a TypeB,
        since there is a TypeA two levels up.  Since it has been
        commented out, an exception should be raised.

        """
        confp = YamlConfigParser()
        confp.add_rule('TypeA.*.TypeA.*.TypeA.*', path_type=int)
        confp.add_rule('TypeA.*.TypeA.*.TypeB.*', path_type=int)
        confp.add_rule('TypeA.*.TypeB.*.TypeC.*', path_type=int)
        confp.add_rule('TypeB.*.TypeC.*.TypeC.*', path_type=int)
        self._test_conf_bad(
            confp=confp,
            conftext="""
            TypeA:
              xxxxx:
                TypeA:
                  xxxxx:
                    TypeA:
                      xxxxx: 1
                      yyyyy: 2
                      zzzzz: 3
                    TypeB:
                      xxxxx: 4
                      yyyyy: 5
                  yyyyy:
                    TypeA:
                      xxxxx: 6
                    # TypeB:
                    #   xxxxx: 7
                TypeB:
                  xxxxx:
                    TypeC:
                      xxxxx: 8
                      yyyyy: 9
                  yyyyy:
                    TypeC:
                      xxxxx: 10
            TypeB:
              xxxxx:
                TypeC:
                  xxxxx:
                    TypeC:
                      xxxxx: 11
                  yyyyy:
                    TypeC:
                      xxxxx: 12
                  zzzzz:
                    TypeC:
                      xxxxx: 13
              yyyyy:
                TypeC:
                  xxxxx:
                    TypeC:
                      xxxxx: 14
            """,
            excrex='"TypeA.xxxxx.TypeA.yyyyy.TypeB" is missing')

    def test_wildcard_root_map_with_fixed_path_good_1(self):
        """Test fixed with wildcard on root map accepts single field."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('*')
        conf = self._test_conf_good(confp, """
        aaa: aaaaa
        reqfield: bbbbb
        """)
        self.assertListEqual(list(conf), ['reqfield', 'aaa'])
        self.assertEqual(conf.reqfield, 'bbbbb')
        self.assertEqual(conf.aaa, 'aaaaa')

    def test_wildcard_root_map_with_fixed_path_good_2(self):
        """Test fixed with wildcard on root map accepts multiple fields."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('*')
        conf = self._test_conf_good(confp, """
        aaa: aaaaa
        bbb: bbbbb
        ccc: ccccc
        reqfield: ddddd
        """)
        self.assertSetEqual(set(conf), {'reqfield', 'aaa', 'bbb', 'ccc'})
        self.assertEqual(conf.reqfield, 'ddddd')
        self.assertEqual(conf.aaa, 'aaaaa')
        self.assertEqual(conf.bbb, 'bbbbb')
        self.assertEqual(conf.ccc, 'ccccc')

    def test_wildcard_root_map_with_fixed_path_bad(self):
        """Test fixed with wildcard on nested map rejects no field."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('*')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            """,
            excrex='must contain at least one additional field')

    def test_wildcard_leaf_map_with_fixed_path_good_1(self):
        """Test fixed with wildcard on nested map accepts single field."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.reqfield')
        confp.add_rule('aaa.aaa.*')
        conf = self._test_conf_good(confp, """
        aaa:
          aaa:
            aaa: aaaaa
            reqfield: bbbbb
        """)
        self.assertIsInstance(conf.aaa.aaa, YamlConfig)
        self.assertListEqual(list(conf.aaa.aaa), ['reqfield', 'aaa'])
        self.assertEqual(conf.aaa.aaa.reqfield, 'bbbbb')
        self.assertEqual(conf.aaa.aaa.aaa, 'aaaaa')

    def test_wildcard_leaf_map_with_fixed_path_good_2(self):
        """Test fixed with wildcard on nested map accepts multiple fields."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.reqfield')
        confp.add_rule('aaa.aaa.*')
        conf = self._test_conf_good(confp, """
        aaa:
          aaa:
            aaa: aaaaa
            bbb: bbbbb
            ccc: ccccc
            reqfield: ddddd
        """)
        self.assertIsInstance(conf.aaa.aaa, YamlConfig)
        self.assertSetEqual(set(conf.aaa.aaa), {
            'reqfield', 'aaa', 'bbb', 'ccc'})
        self.assertEqual(conf.aaa.aaa.reqfield, 'ddddd')
        self.assertEqual(conf.aaa.aaa.aaa, 'aaaaa')
        self.assertEqual(conf.aaa.aaa.bbb, 'bbbbb')
        self.assertEqual(conf.aaa.aaa.ccc, 'ccccc')

    def test_wildcard_leaf_map_with_fixed_path_bad(self):
        """Test fixed with wildcard on nested map rejects no field."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.reqfield')
        confp.add_rule('aaa.aaa.*')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                reqfield: aaaaa
            """,
            excrex='must contain at least one additional field')

    def test_wildcard_nested_map_with_fixed_path_good_1(self):
        """Test fixed with wildcard on path of map accepts single field."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.reqfield.aaa')
        confp.add_rule('aaa.*.aaa')
        conf = self._test_conf_good(confp, """
        aaa:
          aaa:
            aaa: aaaaa
          reqfield:
            aaa: bbbbb
        """)
        self.assertIsInstance(conf.aaa, YamlConfig)
        self.assertListEqual(list(conf.aaa), ['reqfield', 'aaa'])
        self.assertEqual(conf.aaa.reqfield.aaa, 'bbbbb')
        self.assertEqual(conf.aaa.aaa.aaa, 'aaaaa')

    def test_wildcard_nested_map_with_fixed_path_good_2(self):
        """Test fixed with wildcard on path of map accepts multiple fields."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.reqfield.aaa')
        confp.add_rule('aaa.*.aaa')
        conf = self._test_conf_good(confp, """
        aaa:
          aaa:
            aaa: aaaaa
          bbb:
            aaa: bbbbb
          ccc:
            aaa: ccccc
          reqfield:
            aaa: ddddd
        """)
        self.assertIsInstance(conf.aaa, YamlConfig)
        self.assertSetEqual(set(conf.aaa), {'reqfield', 'aaa', 'bbb', 'ccc'})
        self.assertEqual(conf.aaa.reqfield.aaa, 'ddddd')
        self.assertEqual(conf.aaa.aaa.aaa, 'aaaaa')
        self.assertEqual(conf.aaa.bbb.aaa, 'bbbbb')
        self.assertEqual(conf.aaa.ccc.aaa, 'ccccc')

    def test_wildcard_nested_map_with_fixed_path_bad(self):
        """Test fixed with wildcard on path of map rejects no field."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.reqfield.aaa')
        confp.add_rule('aaa.*.aaa')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              reqfield:
                aaa: aaaaa
            """,
            excrex='must contain at least one additional field')

    def test_wildcard_root_list_with_fixed_path_good_1(self):
        """Test fixed with wildcard on root list accepts single field."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('*')
        conf = self._test_conf_good(confp, """
        - aaaaa
        - bbbbb
        """)
        self.assertListEqual(list(conf), ['0', '1'])
        self.assertEqual(conf[0], 'aaaaa')
        self.assertEqual(conf[1], 'bbbbb')

    def test_wildcard_root_list_with_fixed_path_good_2(self):
        """Test fixed with wildcard on root list accepts multiple fields."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('*')
        conf = self._test_conf_good(confp, """
        - aaaaa
        - bbbbb
        - ccccc
        - ddddd
        """)
        self.assertListEqual(list(conf), ['0', '1', '2', '3'])
        self.assertEqual(conf[0], 'aaaaa')
        self.assertEqual(conf[1], 'bbbbb')
        self.assertEqual(conf[2], 'ccccc')
        self.assertEqual(conf[3], 'ddddd')

    def test_wildcard_root_list_with_fixed_path_bad(self):
        """Test fixed with wildcard on nested list rejects no field."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('*')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            - aaaaa
            """,
            excrex='must contain at least one additional field')

    def test_wildcard_leaf_list_with_fixed_path_good_1(self):
        """Test fixed with wildcard on nested list accepts single field."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0')
        confp.add_rule('0.0.*')
        conf = self._test_conf_good(confp, """
        - - - aaaaa
            - bbbbb
        """)
        self.assertIsInstance(conf[0][0], YamlConfigList)
        self.assertListEqual(list(conf[0][0]), ['0', '1'])
        self.assertEqual(conf[0][0][0], 'aaaaa')
        self.assertEqual(conf[0][0][1], 'bbbbb')

    def test_wildcard_leaf_list_with_fixed_path_good_2(self):
        """Test fixed with wildcard on nested list accepts multiple fields."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0')
        confp.add_rule('0.0.*')
        conf = self._test_conf_good(confp, """
        - - - aaaaa
            - bbbbb
            - ccccc
            - ddddd
        """)
        self.assertIsInstance(conf[0][0], YamlConfigList)
        self.assertListEqual(list(conf[0][0]), ['0', '1', '2', '3'])
        self.assertEqual(conf[0][0][0], 'aaaaa')
        self.assertEqual(conf[0][0][1], 'bbbbb')
        self.assertEqual(conf[0][0][2], 'ccccc')
        self.assertEqual(conf[0][0][3], 'ddddd')

    def test_wildcard_leaf_list_with_fixed_path_bad_1(self):
        """Test fixed with wildcard on nested list rejects no field."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0')
        confp.add_rule('0.0.*')
        self._test_conf_bad(
            confp=confp,
            conftext='- - - aaaaa',
            excrex='must contain at least one additional field')

    def test_wildcard_nested_list_with_fixed_path_good_1(self):
        """Test fixed with wildcard on path of list accepts single field."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0')
        confp.add_rule('0.*.0')
        conf = self._test_conf_good(confp, """
        - - - aaaaa
          - - bbbbb
        """)
        self.assertIsInstance(conf[0], YamlConfigList)
        self.assertListEqual(list(conf[0]), ['0', '1'])
        self.assertEqual(conf[0][0][0], 'aaaaa')
        self.assertEqual(conf[0][1][0], 'bbbbb')

    def test_wildcard_nested_list_with_fixed_path_good_2(self):
        """Test fixed with wildcard on path of list accepts multiple fields."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0')
        confp.add_rule('0.*.0')
        conf = self._test_conf_good(confp, """
        - - - aaaaa
          - - bbbbb
          - - ccccc
          - - ddddd
        """)
        self.assertIsInstance(conf[0], YamlConfigList)
        self.assertListEqual(list(conf[0]), ['0', '1', '2', '3'])
        self.assertEqual(conf[0][0][0], 'aaaaa')
        self.assertEqual(conf[0][1][0], 'bbbbb')
        self.assertEqual(conf[0][2][0], 'ccccc')
        self.assertEqual(conf[0][3][0], 'ddddd')

    def test_wildcard_nested_list_with_fixed_path_bad(self):
        """Test fixed with wildcard on path of list rejects no field."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0')
        confp.add_rule('0.*.0')
        self._test_conf_bad(
            confp=confp,
            conftext='- - - aaaaa',
            excrex='must contain at least one additional field')


class PathNestingLimits(TestCase):
    """Test that deeply and/or broadly nested maps and lists are supported."""

    @staticmethod
    def _set_nested_value(rec, path, value, dtype=dict, depth=0):
        """De-index highly nested record and assign value to the path."""
        # pylint: disable=too-many-branches
        assert len(path) > 0

        # Allow dtype to be a tuple of types, in which case the type
        # is the tuple element corresponding to the depth (modulo
        # tuple length).  This is all to support testing of deeply
        # interleaved maps and lists.
        if isinstance(dtype, tuple):
            dtype0 = dtype[depth % len(dtype)]
            dtype1 = dtype[(depth+1) % len(dtype)]
        else:
            dtype0 = dtype
            dtype1 = dtype

        if dtype0 == dict:
            if len(path) == 1:
                rec[path[0]] = value
            else:
                if not path[0] in rec:
                    rec[path[0]] = dtype1()
                PathNestingLimits._set_nested_value(
                    rec[path[0]], path[1:], value, dtype, depth=depth+1)

        elif dtype0 == list:
            assert path[0] <= len(rec)+1
            if len(path) == 1:
                if len(rec) <= path[0]:
                    rec.append(value)
                else:
                    rec[path[0]] = value
            else:
                if len(rec) <= path[0]:
                    rec.append(dtype1())
                PathNestingLimits._set_nested_value(
                    rec[path[0]], path[1:], value, dtype, depth=depth+1)

        else:
            raise RuntimeError('Bad dtype={0}'.format(dtype0))

    @staticmethod
    def _del_nested_value(rec, path):
        """Locate the value at the path and delete it, splicing for a list."""
        assert len(path) > 0
        if len(path) == 1:
            del rec[path[0]]
        else:
            PathNestingLimits._del_nested_value(rec[path[0]], path[1:])
            if len(rec[path[0]]) == 0:
                del rec[path[0]]

    @staticmethod
    def _get_nested_value(rec, path):
        """De-index highly nested record and retrieve value at path."""
        assert len(path) > 0
        if len(path) == 1:
            return rec[path[0]]
        return PathNestingLimits._get_nested_value(rec[path[0]], path[1:])

    @staticmethod
    def _generate_path_combos(maxdepth, nbranches, ptype=int):
        """Generate every path combo with the given parameters.

        Generate every possible path of depth maxdepth with
        nbranches branches at each step.  If ptype is int, then
        the branch names will be integers (0, 1, 2, etc).  If ptype is
        str, then the branch names will be letters ('a', 'b', 'c',
        etc).  If ptype is a tuple such as (str, int), then the
        branch names at each level will alternate between letters and
        integers (i.e., a combo will look something like ('a', 0, 'a',
        1, 'b').  These path combos are for use building both highly
        and broadly nested conffiles and for configuring parsers to
        accept them.

        """
        # Allow ptype to be:
        #  int - with unlimited branching
        #  str - with 'a'..'z' + 'A'..'Z' + '0'..'9' branching
        #  a tuple of both, which will interleave numbers and letters in path
        assert maxdepth >= 1
        if isinstance(ptype, tuple):
            for ptypei in ptype:
                assert ptypei in (int, str)
        else:
            assert ptype in (int, str)
        strords = (
            list(range(ord('a'), ord('z')+1)) +
            list(range(ord('A'), ord('Z')+1)) +
            list(range(ord('0'), ord('9')+1)))
        if isinstance(ptype, tuple) or ptype == str:
            assert nbranches < len(strords)

        # Use itertools to generate the combinatorial product of
        # nbranches, repeated maxdepth times.  Translate the integers
        # into the proper type, determined by ptype (and modular
        # arithmetic if ptype is a tuple).  Yield a tuple containing
        # the actual path.  Iteration will eventually generate all
        # paths.
        for intcombo in itertools.product(range(nbranches), repeat=maxdepth):
            combo = []
            for depth, intval in enumerate(intcombo):
                if isinstance(ptype, tuple):
                    ptypei = ptype[depth % len(ptype)]
                else:
                    ptypei = ptype
                if ptypei == str:
                    combo.append(chr(strords[intval]))
                else:
                    combo.append(intval)
            yield tuple(combo)

    def _generate_nesting(self, maxdepth, nbranches, ptype):
        """Generate a record with given depth, breadth, and type.

        All of the nesting tests have the same form with different
        parameters, as implemented by this function.  They call
        _generate_path_combos with parameters to generate a sequence
        of deeply or broadly nested paths, with int-type, str-type, or
        both.  Then they use those paths to configure a parser,
        generate a record structure with the paths to be written to a
        conffile, and construct a list of the expected test results.
        This function performs that common construction of parser,
        record, and test results to be used in both tests of success
        and failure.

        """
        # Initial setup
        confp = YamlConfigParser()
        conf_tests = []

        # Derive the data type of the record from ptype
        if ptype == str:
            conf_record = {}
            dtype = dict
        elif ptype == int:
            conf_record = []
            dtype = list
        else:
            assert isinstance(ptype, tuple)
            conf_record = {} if ptype[0] == str else []
            dtype = tuple((dict if typ == str else list for typ in ptype))

        # Generate all combos and use the index of the combo as the path value
        for value, combo in enumerate(self._generate_path_combos(
                maxdepth=maxdepth, nbranches=nbranches, ptype=ptype)):

            # Construct the rule path for add_rule, converting any ints to strs
            rule_path = '.'.join([str(idx) for idx in combo])

            # Add the rule path to the parser
            confp.add_rule(rule_path)

            # Add the value to the conffile record
            self._set_nested_value(conf_record, combo, value, dtype)

            # Record the path and value so the conf object can be tested
            conf_tests.append((combo, value))

        return confp, conf_record, conf_tests

    def _test_good_nesting(self, maxdepth, nbranches, ptype):
        """Generate and test nested config as described and expect success.

        Call the nesting generator to configure the parser, generate the
        conffile record, and compile the test key.  The record is
        written to a conffile, and the parser is applied to that
        conffile.  The values at the paths in the resulting conf
        object are checked against the values returned by
        _generate_path_combos for correctness.

        """
        # Generate nesting
        confp, conf_record, conf_tests = self._generate_nesting(
            maxdepth, nbranches, ptype)

        # Serialize the record into the conffile and then parse it back in
        self._write_file(self.conffile, yaml.safe_dump(conf_record))
        conf = confp.parse_file(self.conffile)

        # Loop through each value and test that the path has the proper value
        for combo, value in conf_tests:
            rule_path = '.'.join([str(idx) for idx in combo])
            self.assertEqual(
                self._get_nested_value(conf, combo), value,
                msg='{0}: conf.{1} != {2}'.format(
                    self.conffile, rule_path, value))

    def _test_bad_nesting(self, maxdepth, nbranches, ptype, delindex):
        """Generate and test nested config as described and expect failure.

        Call the nesting generator to configure the parser.  Before
        writing the conffile, delete the paths corresponding to the
        given index (by looking up the corresponding path in the test
        list).  Write the conffile, attempt to parse it, and check
        whether the parse fails because the given path is missing.

        """
        # Generate nesting
        confp, conf_record, conf_tests = self._generate_nesting(
            maxdepth, nbranches, ptype)

        # Identify and delete the given path
        combo, _ = conf_tests[delindex]
        self._del_nested_value(conf_record, combo)
        del_path = '.'.join([str(idx) for idx in combo])

        # Serialize the record into the conffile
        self._write_file(self.conffile, yaml.safe_dump(conf_record))

        # Attempt to parse the conffile and confirm the missing field
        # exactly confirming the path for maps (str) but only the fact
        # of a missing field for lists (int) and mixed because in
        # those cases the deletion changes around index numbers.
        if ptype == str:
            with self.assertRaisesRegex(
                    ParseError, '"{0}" is missing'.format(del_path)):
                confp.parse_file(self.conffile)
        else:
            with self.assertRaisesRegex(ParseError, 'is missing'):
                confp.parse_file(self.conffile)

    def test_field_nesting_limits_deep_maps_good(self):
        """Test maps of depth 8 with 2 branches each level are supported."""
        self._test_good_nesting(maxdepth=8, nbranches=2, ptype=str)

    def test_field_nesting_limits_deep_maps_bad(self):
        """Test deep maps detect a missing field."""
        self._test_bad_nesting(
            maxdepth=8, nbranches=2, ptype=str, delindex=-10)

    def test_field_nesting_limits_deep_lists_good(self):
        """Test lists of depth 8 with 2 branches each level are supported."""
        self._test_good_nesting(maxdepth=8, nbranches=2, ptype=int)

    def test_field_nesting_limits_deep_lists_bad(self):
        """Test deep lists detect a missing field."""
        self._test_bad_nesting(
            maxdepth=8, nbranches=2, ptype=int, delindex=-10)

    def test_field_nesting_limits_deep_mixed_good(self):
        """Test mixed structures of depth 8 with 2 branches are supported."""
        self._test_good_nesting(maxdepth=8, nbranches=2, ptype=(str, int))

    def test_field_nesting_limits_deep_mixed_bad(self):
        """Test deep mixed structures detect a missing field."""
        self._test_bad_nesting(
            maxdepth=8, nbranches=2, ptype=(str, int), delindex=-10)

    def test_field_nesting_limits_broad_maps_good(self):
        """Test maps of depth 3 with 10 branches each level are supported."""
        self._test_good_nesting(maxdepth=3, nbranches=10, ptype=str)

    def test_field_nesting_limits_broad_maps_bad(self):
        """Test broad maps detect a missing field."""
        self._test_bad_nesting(
            maxdepth=3, nbranches=10, ptype=str, delindex=-10)

    def test_field_nesting_limits_broad_lists_good(self):
        """Test lists of depth 3 with 10 branches each level are supported."""
        self._test_good_nesting(maxdepth=3, nbranches=10, ptype=int)

    def test_field_nesting_limits_broad_lists_bad(self):
        """Test broad lists detect a missing field."""
        self._test_bad_nesting(
            maxdepth=3, nbranches=10, ptype=int, delindex=-10)

    def test_field_nesting_limits_broan_mixed_good(self):
        """Test mixed structures of depth 3 with 10 are supported."""
        self._test_good_nesting(maxdepth=3, nbranches=10, ptype=(str, int))

    def test_field_nesting_limits_broad_mixed_bad(self):
        """Test broad mixed structures detect a missing field."""
        self._test_bad_nesting(
            maxdepth=3, nbranches=10, ptype=(str, int), delindex=-10)


class RulePathNoFollowBasics(TestCase):
    """Check basic operation of parser nofollow flag."""

    def test_nofollow_root_has_content_good(self):
        """A nofollow root rule should allow arbitrary structure."""
        confp = YamlConfigParser(nofollow=True)
        conf = self._test_conf_good(confp, """
        aaa: aaaaa
        bbb:
        - bbbbb
        - ccccc
        - ddddd
        """)
        self.assertIsInstance(conf, YamlConfig)
        self.assertEqual(conf.aaa, 'aaaaa')
        self.assertEqual(conf.bbb[0], 'bbbbb')
        self.assertEqual(conf.bbb[1], 'ccccc')
        self.assertEqual(conf.bbb[2], 'ddddd')

    def test_nofollow_on_root_empty_map_good(self):
        """A nofollow root rule should allow an empty map."""
        confp = YamlConfigParser(nofollow=True)
        conf = self._test_conf_good(confp, '{}')
        self.assertIsInstance(conf, YamlConfig)
        self.assertEqual(len(conf), 0)

    def test_nofollow_on_root_empty_list_good(self):
        """A nofollow root rule should allow an empty list."""
        confp = YamlConfigParser(nofollow=True)
        conf = self._test_conf_good(confp, '[]')
        self.assertIsInstance(conf, YamlConfigList)
        self.assertEqual(len(conf), 0)

    def test_nofollow_on_root_empty_file_bad(self):
        """A nofollow root rule should still reject an empty list."""
        confp = YamlConfigParser(nofollow=True)
        self._test_conf_bad(
            confp=confp,
            conftext='',
            excrex='config cannot be empty or null')

    def test_nofollow_on_map_has_contents_good(self):
        """A nofollow map path should allow arbitrary substructure."""
        confp = YamlConfigParser()
        confp.add_rule('noffield', nofollow=True)
        conf = self._test_conf_good(confp, """
        noffield:
          aaa: aaaaa
          bbb:
          - bbbbb
          - ccccc
          - ddddd
        """)
        self.assertListEqual(list(conf), ['noffield'])
        self.assertIsInstance(conf.noffield, dict)
        self.assertEqual(conf.noffield['aaa'], 'aaaaa')
        self.assertEqual(conf.noffield['bbb'][0], 'bbbbb')
        self.assertEqual(conf.noffield['bbb'][1], 'ccccc')
        self.assertEqual(conf.noffield['bbb'][2], 'ddddd')

    def test_nofollow_on_map_null_field_good(self):
        """A nofollow map path should allow a null field."""
        confp = YamlConfigParser()
        confp.add_rule('noffield', nofollow=True)
        conf = self._test_conf_good(confp, 'noffield:')
        self.assertListEqual(list(conf), ['noffield'])
        self.assertIsNone(conf.noffield)

    def test_nofollow_on_map_empty_map_good(self):
        """A nofollow map path should allow an empty map."""
        confp = YamlConfigParser()
        confp.add_rule('noffield', nofollow=True)
        conf = self._test_conf_good(confp, 'noffield: {}')
        self.assertListEqual(list(conf), ['noffield'])
        self.assertIsInstance(conf.noffield, dict)
        self.assertEqual(len(conf.noffield), 0)

    def test_nofollow_on_map_empty_list_good(self):
        """A nofollow map path should allow an empty list."""
        confp = YamlConfigParser()
        confp.add_rule('noffield', nofollow=True)
        conf = self._test_conf_good(confp, 'noffield: []')
        self.assertListEqual(list(conf), ['noffield'])
        self.assertIsInstance(conf.noffield, list)
        self.assertEqual(len(conf.noffield), 0)


class RulePathOptionalBasics(TestCase):
    """Check basic operation of parser optional flag."""

    def test_optional_at_root_map_present_vs_absent_good(self):
        """Optional at the root level of a map should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('opt_present', optional=True)
        confp.add_rule('opt_missing', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext='opt_present: aaaaa')
        self.assertListEqual(list(conf), ['opt_present', 'opt_missing'])
        self.assertEqual(conf.opt_present, 'aaaaa')
        self.assertIsNone(conf.opt_missing)

    def test_optional_at_root_map_empty_hash_good(self):
        """Optional at the root level should support empty-hash config."""
        confp = YamlConfigParser()
        confp.add_rule('opt_a', optional=True)
        confp.add_rule('opt_b', optional=True)
        confp.add_rule('opt_c', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext='{}')
        self.assertListEqual(list(conf), ['opt_a', 'opt_b', 'opt_c'])
        self.assertIsNone(conf.opt_a)
        self.assertIsNone(conf.opt_b)
        self.assertIsNone(conf.opt_c)

    def test_optional_at_leaf_of_map_presence_vs_absence_good(self):
        """Optional at leaf of a map should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.opt_present', optional=True)
        confp.add_rule('aaa.aaa.opt_missing', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                opt_present: aaaaa
            """)
        self.assertListEqual(list(conf.aaa.aaa), ['opt_present', 'opt_missing'])
        self.assertEqual(conf.aaa.aaa.opt_present, 'aaaaa')
        self.assertIsNone(conf.aaa.aaa.opt_missing)

    def test_optional_at_leaf_of_map_empty_hash_good(self):
        """Optional at the leaf of a map should support empty-hash config."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.opt_a', optional=True)
        confp.add_rule('aaa.aaa.opt_b', optional=True)
        confp.add_rule('aaa.aaa.opt_c', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            aaa:
              aaa: {}
            """)
        self.assertListEqual(list(conf.aaa.aaa), ['opt_a', 'opt_b', 'opt_c'])
        self.assertIsNone(conf.aaa.aaa.opt_a)
        self.assertIsNone(conf.aaa.aaa.opt_b)
        self.assertIsNone(conf.aaa.aaa.opt_c)

    def test_optional_at_leaf_of_map_null_leaf_bad(self):
        """Optional at the leaf of a map should reject a null parent."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.opt_a', optional=True)
        confp.add_rule('aaa.aaa.opt_b', optional=True)
        confp.add_rule('aaa.aaa.opt_c', optional=True)
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
            """,
            excrex='"aaa.aaa" is .* but a record or list is expected')

    def test_optional_at_leaf_of_map_null_leaf_optional_parent_good(self):
        """Optional at leaf of map with optional parent should support null."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa', optional=True)
        confp.add_rule('aaa.aaa.opt_a', optional=True)
        confp.add_rule('aaa.aaa.opt_b', optional=True)
        confp.add_rule('aaa.aaa.opt_c', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            aaa:
              aaa:
            """)
        self.assertIsNone(conf.aaa.aaa)

    def test_optional_at_root_list_present_vs_absent_good(self):
        """Optional at the root level of a list should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('0', optional=True)
        confp.add_rule('1', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext='- aaaaa')
        self.assertListEqual(list(conf), ['0', '1'])
        self.assertEqual(conf[0], 'aaaaa')
        self.assertIsNone(conf[1])

    def test_optional_at_root_list_empty_hash_good(self):
        """Optional at the root level should support empty-list config."""
        confp = YamlConfigParser()
        confp.add_rule('0', optional=True)
        confp.add_rule('1', optional=True)
        confp.add_rule('2', optional=True)
        conf = self._test_conf_good(confp, '[]')
        self.assertListEqual(list(conf), ['0', '1', '2'])
        self.assertIsNone(conf[0])
        self.assertIsNone(conf[1])
        self.assertIsNone(conf[2])

    def test_optional_at_leaf_of_list_presence_vs_absence_good(self):
        """Optional at leaf of a list should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0', optional=True)
        confp.add_rule('0.0.1', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            -
              -
                - aaaaa
            """)
        self.assertListEqual(list(conf[0][0]), ['0', '1'])
        self.assertEqual(conf[0][0][0], 'aaaaa')
        self.assertIsNone(conf[0][0][1])

    def test_optional_at_leaf_of_list_empty_list_good(self):
        """Optional at leaf of a list should support empty-list config."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0', optional=True)
        confp.add_rule('0.0.1', optional=True)
        confp.add_rule('0.0.2', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            -
              - []
            """)
        self.assertListEqual(list(conf[0][0]), ['0', '1', '2'])
        self.assertIsNone(conf[0][0][0])
        self.assertIsNone(conf[0][0][1])
        self.assertIsNone(conf[0][0][2])

    def test_optional_at_leaf_of_list_null_leaf_bad(self):
        """Optional at the leaf of a list should reject a null parent."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0', optional=True)
        confp.add_rule('0.0.1', optional=True)
        confp.add_rule('0.0.2', optional=True)
        self._test_conf_bad(
            confp=confp,
            conftext="""
            -
              -
            """,
            excrex='"0.0" is .* but a record or list is expected')

    def test_optional_at_leaf_of_list_null_leaf_optional_parent_good(self):
        """Optional at leaf of list with optional parent should support null."""
        confp = YamlConfigParser()
        confp.add_rule('0.0', optional=True)
        confp.add_rule('0.0.0', optional=True)
        confp.add_rule('0.0.1', optional=True)
        confp.add_rule('0.0.2', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            -
              -
            """)
        self.assertIsNone(conf[0][0])

    def test_optional_map_required_default_children_all_present_good(self):
        """Optional with required and default children specified should work."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optfield', optional=True)
        confp.add_rule('optfield.reqfield')
        confp.add_rule('optfield.deffield', default='zzzzz')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            optfield:
              reqfield: bbbbb
              deffield: ccccc
            """)
        self.assertEqual(conf.reqfield, 'aaaaa')
        self.assertEqual(conf.optfield.reqfield, 'bbbbb')
        self.assertEqual(conf.optfield.deffield, 'ccccc')

    def test_optional_map_required_default_children_default_missing_good(self):
        """Optional with required and default children specified should work."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optfield', optional=True)
        confp.add_rule('optfield.reqfield')
        confp.add_rule('optfield.deffield', default='zzzzz')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            optfield:
              reqfield: bbbbb
            """)
        self.assertEqual(conf.reqfield, 'aaaaa')
        self.assertEqual(conf.optfield.reqfield, 'bbbbb')
        self.assertEqual(conf.optfield.deffield, 'zzzzz')

    def test_optional_map_required_default_children_required_missing_bad(self):
        """Missing required child of present optional should be required."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optfield', optional=True)
        confp.add_rule('optfield.reqfield')
        confp.add_rule('optfield.deffield', default='zzzzz')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            optfield:
              deffield: ccccc
            """,
            excrex='"optfield.reqfield" is missing')

    def test_optional_map_required_default_children_missing_good(self):
        """Required and default children of missing optional should accept."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optfield', optional=True)
        confp.add_rule('optfield.reqfield')
        confp.add_rule('optfield.deffield', default='zzzzz')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            """)
        self.assertEqual(conf.reqfield, 'aaaaa')
        self.assertIsNone(conf.optfield)

    def test_optional_map_required_default_children_null_good(self):
        """Required and default children of null optional should accept."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optfield', optional=True)
        confp.add_rule('optfield.reqfield')
        confp.add_rule('optfield.deffield', default='zzzzz')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            optfield:
            """)
        self.assertEqual(conf.reqfield, 'aaaaa')
        self.assertIsNone(conf.optfield)

    def test_optional_list_required_default_children_all_present_good(self):
        """Optional with required and default children specified should work."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1', optional=True)
        confp.add_rule('1.0')
        confp.add_rule('1.1', default='zzzzz')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            - aaaaa
            -
              - bbbbb
              - ccccc
            """)
        self.assertEqual(conf[0], 'aaaaa')
        self.assertEqual(conf[1][0], 'bbbbb')
        self.assertEqual(conf[1][1], 'ccccc')

    def test_optional_list_required_default_children_default_missing_good(self):
        """Optional with required and default children specified should work."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1', optional=True)
        confp.add_rule('1.0')
        confp.add_rule('1.1', default='zzzzz')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            - aaaaa
            -
              - bbbbb
            """)
        self.assertEqual(conf[0], 'aaaaa')
        self.assertEqual(conf[1][0], 'bbbbb')
        self.assertEqual(conf[1][1], 'zzzzz')

    def test_optional_list_required_default_children_required_missing_bad(self):
        """Missing required child of present optional should be required."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1', optional=True)
        confp.add_rule('1.0')
        confp.add_rule('1.1', default='zzzzz')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            - aaaaa
            - []
            """,
            excrex='"1.0" is missing')

    def test_optional_list_required_default_children_missing_good(self):
        """Required and default children of missing optional should accept."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1', optional=True)
        confp.add_rule('1.0')
        confp.add_rule('1.1', default='zzzzz')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            - aaaaa
            """)
        self.assertEqual(conf[0], 'aaaaa')
        self.assertIsNone(conf[1])

    def test_optional_list_required_default_children_null_good(self):
        """Required and default children of null optional should accept."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1', optional=True)
        confp.add_rule('1.0')
        confp.add_rule('1.1', default='zzzzz')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            - aaaaa
            -
            """)
        self.assertEqual(conf[0], 'aaaaa')
        self.assertIsNone(conf[1])


class RulePathOptionalImplicitRuleChecks(TestCase):
    """Test implicit rules are added when rules for children are added.

    When an optional rule defines implicit fields along the path to
    the optional, the rules for those implicit fields are required.
    To make those implicitly defined paths optional, they need to be
    defined explicitly with the optional flag.

    """

    def test_optional_implicit_rule_option_field_present_good(self):
        """Implicit fields should be accepted when present."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb.ccc.ddd.optfield', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            aaa: aaaaa
            bbb:
              ccc:
                ddd:
                  optfield: bbbbb
            """)
        self.assertEqual(conf.aaa, 'aaaaa')
        self.assertEqual(conf.bbb.ccc.ddd.optfield, 'bbbbb')

    def test_optional_implicit_rule_option_field_empty_good(self):
        """Implicit fields should be accepted with empty-map optional."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb.ccc.ddd.optfield', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            aaa: aaaaa
            bbb:
              ccc:
                ddd:
                  optfield: {}
            """)
        self.assertEqual(conf.aaa, 'aaaaa')
        self.assertEqual(len(conf.bbb.ccc.ddd.optfield), 0)
        self.assertFalse(conf.bbb.ccc.ddd.optfield)

    def test_optional_implicit_rule_option_field_null_good(self):
        """Implicit fields should be accepted with null optional."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb.ccc.ddd.optfield', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            aaa: aaaaa
            bbb:
              ccc:
                ddd:
                  optfield:
            """)
        self.assertEqual(conf.aaa, 'aaaaa')
        self.assertIsNone(conf.bbb.ccc.ddd.optfield)

    def test_optional_implicit_rule_option_field_missing_bad_1(self):
        """Implicit fields should reject missing optional."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb.ccc.ddd.optfield', optional=True)
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa: aaaaa
            bbb:
              ccc:
                ddd:
            """,
            excrex='"bbb.ccc.ddd" is .* but a record or list is expected')

    def test_optional_implicit_rule_option_field_missing_bad_2(self):
        """Implicit fields should reject missing path fields."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb.ccc.ddd.optfield', optional=True)
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa: aaaaa
            bbb:
              ccc:
            """,
            excrex='"bbb.ccc" is .* but a record or list is expected')

    def test_optional_implicit_rule_option_field_missing_bad_3(self):
        """Implicit fields should reject missing path fields."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb.ccc.ddd.optfield', optional=True)
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa: aaaaa
            bbb:
            """,
            excrex='"bbb" is .* but a record or list is expected')

    def test_optional_implicit_rule_option_field_missing_bad_4(self):
        """Implicit fields should reject missing path fields."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb.ccc.ddd.optfield', optional=True)
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa: aaaaa
            """,
            excrex='"bbb" is missing')

    def test_optional_implicit_rule_full_path_optional_good_1(self):
        """Optional path should permit nulls at any point along the path."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb', optional=True)
        confp.add_rule('bbb.ccc', optional=True)
        confp.add_rule('bbb.ccc.ddd', optional=True)
        confp.add_rule('bbb.ccc.ddd.optfield', optional=True)
        conf = self._test_conf_good(confp, """
        aaa: aaaaa
        """)
        self.assertIsNone(conf.bbb)

    def test_optional_implicit_rule_full_path_optional_good_2(self):
        """Optional path should permit nulls at any point along the path."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb', optional=True)
        confp.add_rule('bbb.ccc', optional=True)
        confp.add_rule('bbb.ccc.ddd', optional=True)
        confp.add_rule('bbb.ccc.ddd.optfield', optional=True)
        conf = self._test_conf_good(confp, """
        aaa: aaaaa
        bbb:
        """)
        self.assertIsNone(conf.bbb)

    def test_optional_implicit_rule_full_path_optional_good_3(self):
        """Optional path should permit nulls at any point along the path."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb', optional=True)
        confp.add_rule('bbb.ccc', optional=True)
        confp.add_rule('bbb.ccc.ddd', optional=True)
        confp.add_rule('bbb.ccc.ddd.optfield', optional=True)
        conf = self._test_conf_good(confp, """
        aaa: aaaaa
        bbb:
          ccc:
        """)
        self.assertIsNone(conf.bbb.ccc)

    def test_optional_implicit_rule_full_path_optional_good_4(self):
        """Optional path should permit nulls at any point along the path."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb', optional=True)
        confp.add_rule('bbb.ccc', optional=True)
        confp.add_rule('bbb.ccc.ddd', optional=True)
        confp.add_rule('bbb.ccc.ddd.optfield', optional=True)
        conf = self._test_conf_good(confp, """
        aaa: aaaaa
        bbb:
          ccc:
            ddd:
        """)
        self.assertIsNone(conf.bbb.ccc.ddd)

    def test_optional_implicit_rule_full_path_optional_good_5(self):
        """Optional path should permit nulls at any point along the path."""
        confp = YamlConfigParser()
        confp.add_rule('aaa')
        confp.add_rule('bbb', optional=True)
        confp.add_rule('bbb.ccc', optional=True)
        confp.add_rule('bbb.ccc.ddd', optional=True)
        confp.add_rule('bbb.ccc.ddd.optfield', optional=True)
        conf = self._test_conf_good(confp, """
        aaa: aaaaa
        bbb:
          ccc:
            ddd:
              optfield:
        """)
        self.assertIsNone(conf.bbb.ccc.ddd.optfield)


class RulePathDefaultBasics(TestCase):
    """Check basic operation of parser default flag."""

    def test_default_at_root_map_present_vs_absent_good(self):
        """Default at the root level of a map should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('def_present', default='zzzzz')
        confp.add_rule('def_missing', default='yyyyy')
        conf = self._test_conf_good(confp, 'def_present: aaaaa')
        self.assertListEqual(list(conf), ['def_present', 'def_missing'])
        self.assertEqual(conf.def_present, 'aaaaa')
        self.assertEqual(conf.def_missing, 'yyyyy')

    def test_optional_at_root_list_present_vs_absent_good(self):
        """Default at the root level of a list should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('0', default='zzzzz')
        confp.add_rule('1', default='yyyyy')
        conf = self._test_conf_good(confp, '- aaaaa')
        self.assertListEqual(list(conf), ['0', '1'])
        self.assertEqual(conf[0], 'aaaaa')
        self.assertEqual(conf[1], 'yyyyy')

    def test_default_on_map_path_present_vs_absent_good(self):
        """Default along a path of a map should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.def_present', default='zzzzz')
        confp.add_rule('aaa.aaa.def_missing', default='yyyyy')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                def_present: aaaaa
            """)
        self.assertListEqual(list(conf.aaa.aaa), ['def_present', 'def_missing'])
        self.assertEqual(conf.aaa.aaa.def_present, 'aaaaa')
        self.assertEqual(conf.aaa.aaa.def_missing, 'yyyyy')

    def test_default_on_list_path_present_vs_absent_good(self):
        """Default along a path of a list should be supported."""
        confp = YamlConfigParser()
        confp.add_rule('0.0.0', default='zzzzz')
        confp.add_rule('0.0.1', default='yyyyy')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            -
              -
                - aaaaa
            """)
        self.assertListEqual(list(conf[0][0]), ['0', '1'])
        self.assertEqual(conf[0][0][0], 'aaaaa')
        self.assertEqual(conf[0][0][1], 'yyyyy')

    def test_default_with_map_nesting_naive_bad(self):
        """Parser rules should capture default with nested structure."""
        confp = YamlConfigParser()
        confp.add_rule('deffield', default={'aaa': 'aaaaa'})
        self._test_conf_bad(
            confp=confp,
            conftext='deffield:',
            excrex='"deffield.aaa" unexpected by parser')

    def test_default_with_map_nesting_and_parser_rules_good(self):
        """Parser rules should capture default with nested structure."""
        confp = YamlConfigParser()
        confp.add_rule('deffield', default={'aaa': 'aaaaa'})
        confp.add_rule('deffield.aaa')
        conf = self._test_conf_good(
            confp=confp,
            conftext='deffield:')
        self.assertIsInstance(conf.deffield, YamlConfig)
        self.assertEqual(conf.deffield.aaa, 'aaaaa')

    def test_default_with_list_nesting_naive_bad(self):
        """Parser rules should capture default with nested structure."""
        confp = YamlConfigParser()
        confp.add_rule('0', default=['aaaaa'])
        self._test_conf_bad(
            confp=confp,
            conftext='-',
            excrex='"0.0" unexpected by parser')

    def test_default_with_list_nesting_and_parser_rules_good(self):
        """Parser rules should capture default with nested structure."""
        confp = YamlConfigParser()
        confp.add_rule('0', default=['aaaaa'])
        confp.add_rule('0.0')
        conf = self._test_conf_good(confp, '-')
        self.assertIsInstance(conf[0], YamlConfigList)
        self.assertEqual(conf[0][0], 'aaaaa')

    def test_default_null_default_ignored(self):
        """A null default is ignored; optional should be used instead."""
        # A value of 'None' for default actually is default's default,
        # which results in that parameter being a noop, so the field
        # is treated as required by the parser.  An optional field is
        # really what we want.  If it is specified, use it.  If not,
        # it gets created and assigned the value None.  In other
        # words, it 'defaults' to None.

        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('deffield', default=None)
        self._test_conf_bad(
            confp=confp,
            conftext='reqfield:',
            excrex='"deffield" is missing')


class RulePathDefaultWithOptionalAndDefaultChildren(TestCase):
    """Test handling of optional and default children of nested defaults.

    Since default substitution happens from the top down, it is
    possible for a parent default to leave optional or default
    children unspecified, and then their missing behavior will be
    invoked.

    """

    def test_default_with_children_all_present_good(self):
        """When full structure is in config, defaults should be ignored."""
        confp = YamlConfigParser()
        confp.add_rule('deffield', default={'reqfield': 'zzzzz'})
        confp.add_rule('deffield.reqfield')
        confp.add_rule('deffield.optfield', optional=True)
        confp.add_rule('deffield.optfield.reqfield')
        confp.add_rule('deffield.deffield', default={'reqfield': 'yyyyy'})
        confp.add_rule('deffield.deffield.reqfield')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            deffield:
              reqfield: aaaaa
              optfield:
                reqfield: bbbbb
              deffield:
                reqfield: ccccc
            """)
        self.assertIsInstance(conf.deffield, YamlConfig)
        self.assertListEqual(
            list(conf.deffield), ['reqfield', 'optfield', 'deffield'])
        self.assertEqual(conf.deffield.reqfield, 'aaaaa')
        self.assertEqual(conf.deffield.optfield.reqfield, 'bbbbb')
        self.assertEqual(conf.deffield.deffield.reqfield, 'ccccc')

    def test_default_with_children_default_child_missing_good(self):
        """When default child is missing, its default should be exercised."""
        confp = YamlConfigParser()
        confp.add_rule('deffield', default={'reqfield': 'zzzzz'})
        confp.add_rule('deffield.reqfield')
        confp.add_rule('deffield.optfield', optional=True)
        confp.add_rule('deffield.optfield.reqfield')
        confp.add_rule('deffield.deffield', default={'reqfield': 'yyyyy'})
        confp.add_rule('deffield.deffield.reqfield')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            deffield:
              reqfield: aaaaa
              optfield:
                reqfield: bbbbb
            """)
        self.assertIsInstance(conf.deffield, YamlConfig)
        self.assertListEqual(
            list(conf.deffield), ['reqfield', 'optfield', 'deffield'])
        self.assertEqual(conf.deffield.reqfield, 'aaaaa')
        self.assertEqual(conf.deffield.optfield.reqfield, 'bbbbb')
        self.assertEqual(conf.deffield.deffield.reqfield, 'yyyyy')

    def test_default_with_children_parent_missing_good(self):
        """When default child is missing, its default should be exercised."""
        confp = YamlConfigParser()
        confp.add_rule('deffield', default={'reqfield': 'zzzzz'})
        confp.add_rule('deffield.reqfield')
        confp.add_rule('deffield.optfield', optional=True)
        confp.add_rule('deffield.optfield.reqfield')
        confp.add_rule('deffield.deffield', default={'reqfield': 'yyyyy'})
        confp.add_rule('deffield.deffield.reqfield')
        conf = self._test_conf_good(confp, 'deffield:')
        self.assertIsInstance(conf.deffield, YamlConfig)
        self.assertListEqual(
            list(conf.deffield), ['reqfield', 'optfield', 'deffield'])
        self.assertEqual(conf.deffield.reqfield, 'zzzzz')
        self.assertIsNone(conf.deffield.optfield)
        self.assertEqual(conf.deffield.deffield.reqfield, 'yyyyy')


class RulePathNoFollowWithOptionalAndDefault(TestCase):
    """Test that nofollow rules can be optional and have defaults."""

    def test_nofollow_map_without_optional_missing_bad(self):
        """A nofollow rule should still be present in conffile."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('noffield', nofollow=True)
        self._test_conf_bad(
            confp=confp,
            conftext='reqfield: aaaaa',
            excrex='"noffield" is missing')

    def test_nofollow_map_with_optional_missing_good(self):
        """An optional, nofollow rule should allow absence from conffile."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optnoffield', optional=True, nofollow=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext='reqfield: aaaaa')
        self.assertListEqual(list(conf), ['reqfield', 'optnoffield'])
        self.assertIsNone(conf.optnoffield)

    def test_nofollow_map_with_optional_null_good(self):
        """An optional, nofollow rule should be allowed to be null."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optnoffield', optional=True, nofollow=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            optnoffield:
            """)
        self.assertListEqual(list(conf), ['reqfield', 'optnoffield'])
        self.assertIsNone(conf.optnoffield)

    def test_nofollow_map_with_optional_present_good(self):
        """An optional, nofollow rule should allow absence from conffile."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optnoffield', optional=True, nofollow=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            optnoffield:
              aaa: bbbbb
              bbb:
              - ccccc
              - ddddd
            """)
        self.assertListEqual(list(conf), ['reqfield', 'optnoffield'])
        self.assertIsInstance(conf.optnoffield, dict)
        self.assertEqual(conf.optnoffield['aaa'], 'bbbbb')
        self.assertEqual(conf.optnoffield['bbb'][0], 'ccccc')
        self.assertEqual(conf.optnoffield['bbb'][1], 'ddddd')

    def test_nofollow_list_without_optional_missing_bad(self):
        """A nofollow rule should still be present in conffile."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1', nofollow=True)
        self._test_conf_bad(
            confp=confp,
            conftext='- aaaaa',
            excrex='"1" is missing')

    def test_nofollow_list_with_optional_missing_good(self):
        """An optional, nofollow rule should allow absence from conffile."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1', optional=True, nofollow=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext='- aaaaa')
        self.assertListEqual(list(conf), ['0', '1'])
        self.assertIsNone(conf[1])

    def test_nofollow_list_with_optional_present_good(self):
        """An optional, nofollow rule should allow absence from conffile."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1', optional=True, nofollow=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            - aaaaa
            - aaa: bbbbb
              bbb:
              - ccccc
              - ddddd
            """)
        self.assertListEqual(list(conf), ['0', '1'])
        self.assertIsInstance(conf[1], dict)
        self.assertEqual(conf[1]['aaa'], 'bbbbb')
        self.assertEqual(conf[1]['bbb'][0], 'ccccc')
        self.assertEqual(conf[1]['bbb'][1], 'ddddd')

    def test_nofollow_map_with_default_missing_good(self):
        """A nofollow rule with a default should allow absence from conffile."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('defnoffield', nofollow=True, default={
            'zzz': 'zzzzz',
            'yyy': ['yyyyy', 'xxxxx']})
        conf = self._test_conf_good(confp, 'reqfield: aaaaa')
        self.assertListEqual(list(conf), ['reqfield', 'defnoffield'])
        self.assertEqual(conf.defnoffield['zzz'], 'zzzzz')
        self.assertEqual(conf.defnoffield['yyy'][0], 'yyyyy')
        self.assertEqual(conf.defnoffield['yyy'][1], 'xxxxx')

    def test_nofollow_map_with_default_present_good(self):
        """A nofollow rule with a default should allow presence in conffile."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('defnoffield', nofollow=True, default={
            'zzz': 'zzzzz',
            'yyy': ['yyyyy', 'xxxxx']})
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            defnoffield:
            - bbbbb
            - aaa: ccccc
              bbb: ddddd
            """)
        self.assertListEqual(list(conf), ['reqfield', 'defnoffield'])
        self.assertIsInstance(conf.defnoffield, list)
        self.assertEqual(conf.defnoffield[0], 'bbbbb')
        self.assertEqual(conf.defnoffield[1]['aaa'], 'ccccc')
        self.assertEqual(conf.defnoffield[1]['bbb'], 'ddddd')


class RulePathOptionalAndDefaultImplementZeroOrMoreWildcards(TestCase):
    """Test zero-or-more implementation using default and optional.

    The recommended way to implement a config path that can have
    zero-or-more fields is by using an optional on the wildcard to
    match one or more fields, and then using either an optional or a
    default on the parent.

    If an optional is used, then a missing parent will be null, while
    an empty parent will be an empty container, but both will evaluate
    as False as an empty-case check that will work in both cases.
    Alternatively, a default specifying an empty container default will
    convert the missing case to the present-but-empty case.  This
    suite of tests establishes operations of such parsers under various
    conditions.

    The various configurations for three parsers are tested in this
    test set:

      allreq: parent and wildcard fields are all required (bad)
      reqpar: parent is required but wildcard fields are optional (bad)
      optpar: parent field is optional as well as and the wildcard fields (good)
      defpar: parent field defaults empty with optional wildcard fields (good)

    """

    def test_zero_or_more_allreq_parser_all_present_map_good(self):
        """Test parser with all fields required accepts full config."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optfield.*')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            optfield:
              aaa: bbbbb
            """)
        self.assertEqual(conf.reqfield, 'aaaaa')
        self.assertTrue(conf.optfield)
        self.assertEqual(len(conf.optfield), 1)

    def test_zero_or_more_reqpar_parser_all_present_map_good(self):
        """Test parser with parent required accepts full config."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optfield.*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            optfield:
              aaa: bbbbb
            """)
        self.assertEqual(conf.reqfield, 'aaaaa')
        self.assertTrue(conf.optfield)
        self.assertEqual(len(conf.optfield), 1)

    def test_zero_or_more_optpar_parser_all_present_map_good(self):
        """Test parser with parent optional accepts full config."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optfield', optional=True)
        confp.add_rule('optfield.*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            optfield:
              aaa: bbbbb
            """)
        self.assertEqual(conf.reqfield, 'aaaaa')
        self.assertTrue(conf.optfield)
        self.assertEqual(len(conf.optfield), 1)

    def test_zero_or_more_defpar_parser_all_present_map_good(self):
        """Test parser with parent default accepts full config."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optfield', default={})
        confp.add_rule('optfield.*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            optfield:
              aaa: bbbbb
            """)
        self.assertEqual(conf.reqfield, 'aaaaa')
        self.assertTrue(conf.optfield)
        self.assertEqual(len(conf.optfield), 1)

    def test_zero_or_more_allreq_parser_empty_optfield_map_bad(self):
        """Test parser with all required rejects empty optional config."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optfield.*')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            optfield: {}
            """,
            excrex='"optfield" must contain at least one field')

    def test_zero_or_more_reqpar_parser_empty_optfield_map_good(self):
        """Test parser with parent required accepts empty optional config."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optfield.*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            optfield: {}
            """)
        self.assertEqual(conf.reqfield, 'aaaaa')
        self.assertFalse(conf.optfield)
        self.assertEqual(len(conf.optfield), 0)

    def test_zero_or_more_optpar_parser_empty_optfield_map_good(self):
        """Test parser with parent optional accepts empty optional config."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optfield', optional=True)
        confp.add_rule('optfield.*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            optfield: {}
            """)
        self.assertEqual(conf.reqfield, 'aaaaa')
        self.assertFalse(conf.optfield)
        self.assertEqual(len(conf.optfield), 0)

    def test_zero_or_more_defpar_parser_empty_optfield_map_good(self):
        """Test parser with parent default accepts empty optional config."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optfield', default={})
        confp.add_rule('optfield.*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            optfield: {}
            """)
        self.assertEqual(conf.reqfield, 'aaaaa')
        self.assertFalse(conf.optfield)
        self.assertEqual(len(conf.optfield), 0)

    def test_zero_or_more_allreq_parser_missing_optfield_map_bad(self):
        """Test parser with all required rejects missing optional config."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optfield.*')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            """,
            excrex='"optfield" is missing')

    def test_zero_or_more_reqpar_parser_missing_optfield_map_bad(self):
        """Test parser with parent required rejects missing optional config."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optfield.*', optional=True)
        self._test_conf_bad(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            """,
            excrex='"optfield" is missing')

    def test_zero_or_more_optpar_parser_missing_optfield_map_good(self):
        """Test parser with parent optional accepts missing optional config."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optfield', optional=True)
        confp.add_rule('optfield.*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            """)
        self.assertEqual(conf.reqfield, 'aaaaa')
        self.assertFalse(conf.optfield)

    def test_zero_or_more_defpar_parser_missing_optfield_map_good(self):
        """Test parser with parent default accepts missing optional config."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('optfield', default={})
        confp.add_rule('optfield.*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            reqfield: aaaaa
            """)
        self.assertEqual(conf.reqfield, 'aaaaa')
        self.assertFalse(conf.optfield)
        self.assertEqual(len(conf.optfield), 0)

    def test_fixed_and_optional_wildcard_empty_at_root_map_good(self):
        """Test parser with required and optional wildcard accepts required."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="reqfield: aaaaa")
        self.assertListEqual(list(conf), ['reqfield'])
        self.assertEqual(conf.reqfield, 'aaaaa')

    def test_fixed_and_optional_wildcard_filled_at_root_map_good_1(self):
        """Test parser with required and optional wildcard accepts both."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            aaa: aaaaa
            reqfield: bbbbb
            """)
        self.assertListEqual(list(conf), ['reqfield', 'aaa'])
        self.assertEqual(conf.reqfield, 'bbbbb')
        self.assertEqual(conf.aaa, 'aaaaa')

    def test_fixed_and_optional_wildcard_filled_at_root_map_good_2(self):
        """Test parser with required and optional wildcard accepts both."""
        confp = YamlConfigParser()
        confp.add_rule('reqfield')
        confp.add_rule('*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            aaa: aaaaa
            bbb: bbbbb
            ccc: ccccc
            reqfield: ddddd
            """)
        self.assertSetEqual(set(conf), {'reqfield', 'aaa', 'bbb', 'ccc'})
        self.assertEqual(conf.reqfield, 'ddddd')
        self.assertEqual(conf.aaa, 'aaaaa')
        self.assertEqual(conf.bbb, 'bbbbb')
        self.assertEqual(conf.ccc, 'ccccc')

    def test_zero_or_more_allreq_parser_all_present_list_good(self):
        """Test parser with all fields required accepts full config."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1.*')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            - aaaaa
            -
              - bbbbb
            """)
        self.assertEqual(conf[0], 'aaaaa')
        self.assertTrue(conf[1])
        self.assertEqual(len(conf[1]), 1)

    def test_zero_or_more_reqpar_parser_all_present_list_good(self):
        """Test parser with parent required accepts full config."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1.*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            - aaaaa
            -
              - bbbbb
            """)
        self.assertEqual(conf[0], 'aaaaa')
        self.assertTrue(conf[1])
        self.assertEqual(len(conf[1]), 1)

    def test_zero_or_more_optpar_parser_all_present_list_good(self):
        """Test parser with parent optional accepts the full config."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1', optional=True)
        confp.add_rule('1.*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            - aaaaa
            -
              - bbbbb
            """)
        self.assertEqual(conf[0], 'aaaaa')
        self.assertTrue(conf[1])
        self.assertEqual(len(conf[1]), 1)

    def test_zero_or_more_defpar_parser_all_present_list_good(self):
        """Test parser with parent default accepts the full config."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1', default={})
        confp.add_rule('1.*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            - aaaaa
            -
              - bbbbb
            """)
        self.assertEqual(conf[0], 'aaaaa')
        self.assertTrue(conf[1])
        self.assertEqual(len(conf[1]), 1)

    def test_zero_or_more_allreq_parser_empty_optfield_list_bad(self):
        """Test parser with all required rejects empty optional config."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1.*')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            - aaaaa
            - []
            """,
            excrex='"1" must contain at least one field')

    def test_zero_or_more_reqpar_parser_empty_optfield_list_good(self):
        """Test parser with parent required accepts empty optional config."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1.*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            - aaaaa
            - []
            """)
        self.assertEqual(conf[0], 'aaaaa')
        self.assertFalse(conf[1])
        self.assertEqual(len(conf[1]), 0)

    def test_zero_or_more_optpar_parser_empty_optfield_list_good(self):
        """Test parser with parent optional accepts empty optional config."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1', optional=True)
        confp.add_rule('1.*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            - aaaaa
            - []
            """)
        self.assertEqual(conf[0], 'aaaaa')
        self.assertFalse(conf[1])
        self.assertEqual(len(conf[1]), 0)

    def test_zero_or_more_defpar_parser_empty_optfield_list_good(self):
        """Test parser with parent default accepts empty optional config."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1', default={})
        confp.add_rule('1.*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            - aaaaa
            - []
            """)
        self.assertEqual(conf[0], 'aaaaa')
        self.assertFalse(conf[1])
        self.assertEqual(len(conf[1]), 0)

    def test_zero_or_more_allreq_parser_missing_optfield_list_bad(self):
        """Test parser with all required rejects missing optional config."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1.*')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            - aaaaa
            """,
            excrex='"1" is missing')

    def test_zero_or_more_reqpar_parser_missing_optfield_list_bad(self):
        """Test parser with parent required rejects missing optional config."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1.*', optional=True)
        self._test_conf_bad(
            confp=confp,
            conftext="""
            - aaaaa
            """,
            excrex='"1" is missing')

    def test_zero_or_more_optpar_parser_missing_optfield_list_good(self):
        """Test parser with parent optional accepts missing optional config."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1', optional=True)
        confp.add_rule('1.*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            - aaaaa
            """)
        self.assertEqual(conf[0], 'aaaaa')
        self.assertFalse(conf[1])

    def test_zero_or_more_defpar_parser_missing_optfield_list_good(self):
        """Test parser with parent optional accepts missing optional config."""
        confp = YamlConfigParser()
        confp.add_rule('0')
        confp.add_rule('1', default={})
        confp.add_rule('1.*', optional=True)
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            - aaaaa
            """)
        self.assertEqual(conf[0], 'aaaaa')
        self.assertFalse(conf[1])
        self.assertEqual(len(conf[1]), 0)


class RulePathWildcardsAndDefaults(TestCase):
    """Test that defaults on a wildcard field are triggered by null values."""

    def test_default_map_with_wildcards_at_toplevel_good(self):
        """A wildcard default should be triggered by explicit defaults."""
        confp = YamlConfigParser()
        confp.add_rule('*', default='zzzzz')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            aaa:
            bbb:
            ccc:
            """)
        self.assertSetEqual(set(conf), {'aaa', 'bbb', 'ccc'})
        self.assertEqual(conf.aaa, 'zzzzz')
        self.assertEqual(conf.bbb, 'zzzzz')
        self.assertEqual(conf.ccc, 'zzzzz')

    def test_default_map_with_wildcards_at_leaf_null_fields_good(self):
        """A wildcard default should be triggered by explicit defaults."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.*', default='zzzzz')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            aaa:
              aaa:
                aaa:
                bbb:
                ccc:
            """)
        self.assertSetEqual(set(conf.aaa.aaa), {'aaa', 'bbb', 'ccc'})
        self.assertEqual(conf.aaa.aaa.aaa, 'zzzzz')
        self.assertEqual(conf.aaa.aaa.bbb, 'zzzzz')
        self.assertEqual(conf.aaa.aaa.ccc, 'zzzzz')

    def test_default_map_with_wildcards_at_empty_leaf_bad(self):
        """A wildcard default should still require one-or-more fields."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.*', default='zzzzz')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa: {}
            """,
            excrex='"aaa.aaa" must contain at least one field')

    def test_default_map_with_wildcards_at_null_leaf_bad_1(self):
        """A wildcard default should still expect a container parent."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.*', default='zzzzz')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
              aaa:
            """,
            excrex='"aaa.aaa" is .* but a record or list is expected')

    def test_default_map_with_wildcards_at_null_leaf_bad_2(self):
        """A wildcard default should still implicitly require parent."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa.*', default='zzzzz')
        self._test_conf_bad(
            confp=confp,
            conftext="""
            aaa:
            """,
            excrex='"aaa" is .* but a record or list is expected')

    def test_default_map_with_wildcards_at_optional_null_leaf_good(self):
        """An optional parent should allow zero-or-more wildcard defaults."""
        confp = YamlConfigParser()
        confp.add_rule('aaa.aaa', optional=True)
        confp.add_rule('aaa.aaa.*', default='zzzzz')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            aaa:
              aaa:
            """)
        self.assertIsNone(conf.aaa.aaa)

    def test_default_map_with_wildcards_uppath(self):
        """Test wildcards 'up-path' from a default are supported."""
        confp = YamlConfigParser()
        confp.add_rule('*.reqfield')
        confp.add_rule('*.deffield', default='zzzzz')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            aaa:
              reqfield: aaaaa
              deffield: bbbbb
            bbb:
              reqfield: ccccc
            """)
        self.assertEqual(conf.aaa.reqfield, 'aaaaa')
        self.assertEqual(conf.aaa.deffield, 'bbbbb')
        self.assertEqual(conf.bbb.reqfield, 'ccccc')
        self.assertEqual(conf.bbb.deffield, 'zzzzz')

    def test_default_map_with_wildcards_downpath(self):
        """Test wildcards 'down-path' from a default are supported."""
        confp = YamlConfigParser()
        confp.add_rule('def_present_map', default={'zzz': 'zzzzz'})
        confp.add_rule('def_present_map.*')
        confp.add_rule('def_present_list', default=['yyyyy', 'xxxxx'])
        confp.add_rule('def_present_list.*')
        confp.add_rule('def_missing_map', default={'www': 'wwwww'})
        confp.add_rule('def_missing_map.*')
        confp.add_rule('def_missing_list', default=['vvvvv', 'uuuuu'])
        confp.add_rule('def_missing_list.*')
        conf = self._test_conf_good(
            confp=confp,
            conftext="""
            def_present_map:
              aaa: aaaaa
              bbb: bbbbb
            def_present_list:
            - ccccc
            """)
        self.assertListEqual(list(conf), [
            'def_present_map', 'def_present_list', 'def_missing_map',
            'def_missing_list'])
        self.assertSetEqual(set(conf.def_present_map), {'aaa', 'bbb'})
        self.assertEqual(conf.def_present_map.aaa, 'aaaaa')
        self.assertEqual(conf.def_present_map.bbb, 'bbbbb')
        self.assertListEqual(list(conf.def_present_list), ['0'])
        self.assertEqual(conf.def_present_list[0], 'ccccc')
        self.assertListEqual(list(conf.def_missing_map), ['www'])
        self.assertEqual(conf.def_missing_map.www, 'wwwww')
        self.assertListEqual(list(conf.def_missing_list), ['0', '1'])
        self.assertEqual(conf.def_missing_list[0], 'vvvvv')
        self.assertEqual(conf.def_missing_list[1], 'uuuuu')


class PathTypeTestNullValues(TestCase):
    """Test that path_type recognizes nulls as NoneTypes."""

    none_type = type(None)

    def test_path_type_null_good_1(self):
        """A none_type should recognize various kinds of null value."""
        conf = self._rule_path_type_good(
            self.none_type, '', 'None', normalizer=str)
        self.assertIsNone(conf.field)

    def test_path_type_null_good_2(self):
        """A none_type should recognize various kinds of null value."""
        conf = self._rule_path_type_good(
            self.none_type, '~', 'None', normalizer=str)
        self.assertIsNone(conf.field)

    def test_path_type_null_good_3(self):
        """A none_type should recognize various kinds of null value."""
        conf = self._rule_path_type_good(
            self.none_type, 'null', 'None', normalizer=str)
        self.assertIsNone(conf.field)

    def test_path_type_null_good_4(self):
        """A none_type should recognize various kinds of null value."""
        conf = self._rule_path_type_good(
            self.none_type, 'NULL', 'None', normalizer=str)
        self.assertIsNone(conf.field)

    def test_path_type_null_good_5(self):
        """A none_type should recognize complex mapping key."""
        confp = YamlConfigParser()
        confp.add_rule('field', path_type=self.none_type)
        conf = self._test_conf_good(confp, '? field')
        self.assertIsNone(conf.field)

    def test_path_type_null_bad_1(self):
        """A none_type should reject things that only look like nulls."""
        self._rule_path_type_bad(
            self.none_type, 'None', 'has type str not type NoneType')

    def test_path_type_null_bad_2(self):
        """A none_type should reject things that only look like nulls."""
        self._rule_path_type_bad(
            self.none_type, '"null"', 'has type str not type NoneType')

    def test_path_type_null_bad_3(self):
        """A none_type should reject things that only look like nulls."""
        self._rule_path_type_bad(
            self.none_type, 'nUll', 'has type str not type NoneType')

    def test_path_type_null_bad_4(self):
        """A none_type should reject things that only look like nulls."""
        self._rule_path_type_bad(
            self.none_type, "'~'", 'has type str not type NoneType')


class PathTypeTestBooleans(TestCase):
    """Test that path_type recognizes booleans."""

    def test_path_type_bool_good_1(self):
        """A bool should recognize booleans."""
        self._rule_path_type_good(bool, 'true', True)

    def test_path_type_bool_good_2(self):
        """A bool should recognize booleans."""
        self._rule_path_type_good(bool, 'True', True)

    def test_path_type_bool_good_3(self):
        """A bool should recognize booleans."""
        self._rule_path_type_good(bool, 'yes', True)

    def test_path_type_bool_good_4(self):
        """A bool should recognize booleans."""
        self._rule_path_type_good(bool, 'ON', True)

    def test_path_type_bool_good_5(self):
        """A bool should recognize booleans."""
        self._rule_path_type_good(bool, 'false', False)

    def test_path_type_bool_good_6(self):
        """A bool should recognize booleans."""
        self._rule_path_type_good(bool, 'False', False)

    def test_path_type_bool_good_7(self):
        """A bool should recognize booleans."""
        self._rule_path_type_good(bool, 'NO', False)

    def test_path_type_bool_good_8(self):
        """A bool should recognize booleans."""
        self._rule_path_type_good(bool, 'off', False)

    def test_path_type_bool_bad_1(self):
        """A bool should reject things that only look like booleans."""
        self._rule_path_type_bad(bool, '"True"', 'has type str not type bool')

    def test_path_type_bool_bad_2(self):
        """A bool should reject things that only look like booleans."""
        self._rule_path_type_bad(bool, 'tRUE', 'has type str not type bool')

    def test_path_type_bool_bad_3(self):
        """A bool should reject things that only  look like booleans."""
        self._rule_path_type_bad(bool, 'nO', 'has type str not type bool')

    def test_path_type_bool_bad_4(self):
        """A bool should reject things that only  look like booleans."""
        self._rule_path_type_bad(bool, '""', 'has type str not type bool')

    def test_path_type_bool_bad_5(self):
        """A bool should reject things that only  look like booleans."""
        self._rule_path_type_bad(bool, '', 'has type NoneType not type bool')

    def test_path_type_bool_bad_6(self):
        """A bool should reject things that only  look like booleans."""
        self._rule_path_type_bad(bool, '1', 'has type int not type bool')

    def test_path_type_bool_bad_7(self):
        """A bool should reject things that only  look like booleans."""
        self._rule_path_type_bad(bool, '0', 'has type int not type bool')


class PathTypeTestStrings(TestCase):
    """Test that path_type recognizes string and unicode types."""

    def test_path_type_str_good_1(self):
        """A str should recognize valid strings."""
        self._rule_path_type_good(str, 'ascii', 'ascii')

    def test_path_type_str_good_2(self):
        """A str should recognize valid strings."""
        self._rule_path_type_good(str, '""', '')

    def test_path_type_str_good_3(self):
        """A str should recognize valid strings."""
        self._rule_path_type_good(str, "''", '')

    def test_path_type_str_good_4(self):
        """A str should recognize valid strings."""
        self._rule_path_type_good(str, '"1.e+2"', '1.e+2')

    @unittest2.skipIf(sys.version_info.major == 2, 'specific to Python 3')
    def test_path_type_str_good_1_py3(self):
        """A str should recognize valid strings."""
        self._rule_path_type_good(str, u'unicØde', 'unicØde')

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_str_bad_1_py2(self):
        """A str should reject unicode strings."""
        self._rule_path_type_bad(
            str, u'unicØde', 'has type unicode not type str')

    def test_path_type_str_bad_1(self):
        """A str should reject integers."""
        self._rule_path_type_bad(str, '42', 'has type int not type str')

    def test_path_type_str_bad_2(self):
        """A str should reject floats."""
        self._rule_path_type_bad(str, '1.e+2', 'has type float not type str')

    def test_path_type_str_bad_3(self):
        """A str should reject null values."""
        self._rule_path_type_bad(str, '', 'has type NoneType not type str')

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_unicode_good_1_py2(self):
        """A unicode should recognize valid unicode strings."""
        # pylint: disable=undefined-variable
        self._rule_path_type_good(unicode, u'unicØde', u'unicØde')

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_unicode_bad_1_py2(self):
        """A unicode should reject str strings."""
        # pylint: disable=undefined-variable
        self._rule_path_type_bad(
            unicode, 'ascii', 'has type str not type unicode')

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_string_union_good_1_py2(self):
        """A str, unicode should recognize both types of strings."""
        # pylint: disable=undefined-variable
        self._rule_path_type_good((str, unicode), 'ascii', 'ascii')

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_string_union_good_2_py2(self):
        """A str, unicode should recognize both types of strings."""
        # pylint: disable=undefined-variable
        self._rule_path_type_good((str, unicode), u'unicØde', u'unicØde')

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_string_union_bad_py2(self):
        """Test that str, unicode rejects non-string."""
        # pylint: disable=undefined-variable
        self._rule_path_type_bad(
            (str, unicode), 42, 'has type int not type str or unicode')

    def test_path_type_str_bad_list_not_str(self):
        """A str should recognize when value is a list structure instead."""
        # Write the file ourselves and configure the parser with
        # nofollow on the rule otherwise we would get an unexpected
        # field error before the typecheck happened.
        self._write_file(self.conffile, """
        field:
        - aaaaa
        - bbbbb
        - ccccc
        """)
        confp = YamlConfigParser()
        confp.add_rule('field', path_type=str, nofollow=True)
        with self.assertRaisesRegex(ParseError, 'has type list not type str'):
            confp.parse_file(self.conffile)

    def test_path_type_str_bad_map_not_str(self):
        """A str should recognize when value is a map structure instead."""
        # Write the file ourselves and configure the parser with
        # nofollow on the rule otherwise we would get an unexpected
        # field error before the typecheck happened.
        self._write_file(self.conffile, """
        field:
          aaa: aaaaa
          bbb: bbbbb
        """)
        confp = YamlConfigParser()
        confp.add_rule('field', path_type=str, nofollow=True)
        with self.assertRaisesRegex(ParseError, 'has type dict not type str'):
            confp.parse_file(self.conffile)


class PathTypeTestNumbers(TestCase):
    """Test that path_type recognizes ints and floats."""

    def test_path_type_int_good_1(self):
        """An int should recognize valid integers."""
        self._rule_path_type_good(int, '42', 42)

    def test_path_type_int_good_2(self):
        """An int should recognize valid integers."""
        self._rule_path_type_good(int, '0', 0)

    def test_path_type_int_good_3(self):
        """An int should recognize valid integers."""
        self._rule_path_type_good(int, '-42', -42)

    def test_path_type_int_good_4(self):
        """An int should recognize valid integers."""
        self._rule_path_type_good(int, '-0', 0)

    def test_path_type_int_good_5(self):
        """An int should recognize valid integers."""
        self._rule_path_type_good(int, '+0', 0)

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_int_good_6_py2(self):
        """An int should recognize valid integers."""
        # pylint: disable=no-member
        self._rule_path_type_good(int, str(sys.maxint), sys.maxint)

    @unittest2.skipIf(sys.version_info.major == 2, 'specific to Python 3')
    def test_path_type_int_good_6_py3(self):
        """An int should recognize valid integers."""
        self._rule_path_type_good(int, str(sys.maxsize), sys.maxsize)

    @unittest2.skipIf(sys.version_info.major == 2, 'specific to Python 3')
    def test_path_type_int_good_7_py3(self):
        """An int should recognize valid integers."""
        self._rule_path_type_good(int, str(sys.maxsize+1), sys.maxsize+1)

    def test_path_type_int_good_one_is_true(self):
        """An int 1 is not a bool but should be recognized as true."""
        conf = self._rule_path_type_good(int, '1', 1)
        self.assertFalse(isinstance(conf.field, bool))
        self.assertTrue(conf.field)

    def test_path_type_int_good_zero_is_false(self):
        """An int 0 is not a bool but should be recognized as false."""
        conf = self._rule_path_type_good(int, '0', 0)
        self.assertFalse(isinstance(conf.field, bool))
        self.assertFalse(conf.field)

    def test_path_type_int_bad_1(self):
        """An int should reject floats."""
        self._rule_path_type_bad(
            int, '0.0', 'has type float not type int')

    def test_path_type_int_bad_2(self):
        """An int should reject strings that look like ints."""
        self._rule_path_type_bad(
            int, '"0"', 'has type str not type int')

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_int_bad_3_py2(self):
        """An int should reject longs that exceed maxint."""
        # pylint: disable=no-member
        self._rule_path_type_bad(
            int, str(sys.maxint+1), 'has type long not type int')

    def test_path_type_float_good_1(self):
        """A float should recognize valid floats."""
        self._rule_path_type_good(float, '42.2', 42.2)

    def test_path_type_float_good_2(self):
        """A float should recognize valid floats."""
        self._rule_path_type_good(float, '1.e+5', 100000)

    def test_path_type_float_good_3(self):
        """A float should recognize infinity."""
        self._rule_path_type_good(float, '.inf', float('inf'))

    def test_path_type_float_good_4(self):
        """A float should recognize negative infinity."""
        self._rule_path_type_good(float, '-.inf', -float('inf'))

    def test_path_type_float_good_5(self):
        """A float should recognize NaNs."""
        self._rule_path_type_good(float, '.nan', 'nan', normalizer=str)

    def test_path_type_float_bad_1(self):
        """A float should reject ints."""
        self._rule_path_type_bad(float, '0', 'has type int not type float')

    def test_path_type_float_bad_2(self):
        """A float should reject strings."""
        self._rule_path_type_bad(float, '1e3', 'has type str not type float')

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_float_bad_3_py2(self):
        """A float should reject ints."""
        # pylint: disable=no-member
        self._rule_path_type_bad(
            float, str(sys.maxint+1), 'has type long not type float')

    @unittest2.skipIf(sys.version_info.major == 2, 'specific to Python 3')
    def test_path_type_float_bad_3_py3(self):
        """A float should reject ints."""
        self._rule_path_type_bad(
            float, str(sys.maxsize+1), 'has type int not type float')

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_long_good_1_py2(self):
        """A long should recognize valid longs."""
        # pylint: disable=undefined-variable, no-member
        self._rule_path_type_good(long, str(sys.maxint+1), sys.maxint+1)

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_long_bad_1_py2(self):
        """A long should reject ints."""
        # pylint: disable=undefined-variable
        self._rule_path_type_bad(long, '0', 'has type int not type long')

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_long_bad_2_py2(self):
        """A long should reject strings."""
        # pylint: disable=undefined-variable
        self._rule_path_type_bad(long, '7L', 'has type str not type long')

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_long_bad_3_py2(self):
        """A long should reject floats."""
        # pylint: disable=undefined-variable
        self._rule_path_type_bad(
            long, '9.223372036854776e+18', 'has type float not type long')

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_numeric_union_good_1_py2(self):
        """An int, long, float should accept variety of numeric types."""
        # pylint: disable=undefined-variable
        self._rule_path_type_good((int, long, float), '42', 42)

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_numeric_union_good_2_py2(self):
        """An int, long, float should accept variety of numeric types."""
        # pylint: disable=undefined-variable
        self._rule_path_type_good((int, long, float), '0', 0)

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_numeric_union_good_3_py2(self):
        """An int, long, float should accept variety of numeric types."""
        # pylint: disable=undefined-variable
        self._rule_path_type_good((int, long, float), '-42', -42)

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_numeric_union_good_4_py2(self):
        """An int, long, float should accept variety of numeric types."""
        # pylint: disable=undefined-variable
        self._rule_path_type_good((int, long, float), '-0', 0)

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_numeric_union_good_5_py2(self):
        """An int, long, float should accept variety of numeric types."""
        # pylint: disable=undefined-variable
        self._rule_path_type_good((int, long, float), '+0', 0)

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_numeric_union_good_6_py2(self):
        """An int, long, float should accept variety of numeric types."""
        # pylint: disable=undefined-variable, no-member
        self._rule_path_type_good(
            (int, long, float), str(sys.maxint), sys.maxint)

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_numeric_union_good_7_py2(self):
        """An int, long, float should accept variety of numeric types."""
        # pylint: disable=undefined-variable
        self._rule_path_type_good((int, long, float), '42.2', 42.2)

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_numeric_union_good_8_py2(self):
        """An int, long, float should accept variety of numeric types."""
        # pylint: disable=undefined-variable
        self._rule_path_type_good((int, long, float), '1.e+5', 100000)

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_numeric_union_good_9_py2(self):
        """An int, long, float should accept variety of numeric types."""
        # pylint: disable=undefined-variable
        self._rule_path_type_good((int, long, float), '.inf', float('inf'))

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_numeric_union_good_10_py2(self):
        """An int, long, float should accept variety of numeric types."""
        # pylint: disable=undefined-variable
        self._rule_path_type_good((int, long, float), '-.inf', -float('inf'))

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_numeric_union_good_11_py2(self):
        """An int, long, float should accept variety of numeric types."""
        # pylint: disable=undefined-variable
        self._rule_path_type_good(
            (int, long, float), '.nan', 'nan', normalizer=str)

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_numeric_union_good_12_py2(self):
        """An int, long, float should accept variety of numeric types."""
        # pylint: disable=undefined-variable, no-member
        self._rule_path_type_good(
            (int, long, float), str(sys.maxint+1), sys.maxint+1)

    @unittest2.skipIf(sys.version_info.major > 2, 'specific to Python 2')
    def test_path_type_numeric_union_bad_py2(self):
        """Test that int, long, float rejects string."""
        # pylint: disable=undefined-variable
        self._rule_path_type_bad(
            (int, long, float), 'forty-two',
            'has type str not type int or long or float')

    @unittest2.skipIf(sys.version_info.major == 2, 'specific to Python 3')
    def test_path_type_numeric_union_good_1_py3(self):
        """An int, float should accept variety of numeric types."""
        self._rule_path_type_good((int, float), '42', 42)

    @unittest2.skipIf(sys.version_info.major == 2, 'specific to Python 3')
    def test_path_type_numeric_union_good_2_py3(self):
        """An int, float should accept variety of numeric types."""
        self._rule_path_type_good((int, float), '0', 0)

    @unittest2.skipIf(sys.version_info.major == 2, 'specific to Python 3')
    def test_path_type_numeric_union_good_3_py3(self):
        """An int, float should accept variety of numeric types."""
        self._rule_path_type_good((int, float), '-42', -42)

    @unittest2.skipIf(sys.version_info.major == 2, 'specific to Python 3')
    def test_path_type_numeric_union_good_4_py3(self):
        """An int, float should accept variety of numeric types."""
        self._rule_path_type_good((int, float), '-0', 0)

    @unittest2.skipIf(sys.version_info.major == 2, 'specific to Python 3')
    def test_path_type_numeric_union_good_5_py3(self):
        """An int, float should accept variety of numeric types."""
        self._rule_path_type_good((int, float), '+0', 0)

    @unittest2.skipIf(sys.version_info.major == 2, 'specific to Python 3')
    def test_path_type_numeric_union_good_6_py3(self):
        """An int, float should accept variety of numeric types."""
        self._rule_path_type_good((int, float), str(sys.maxsize), sys.maxsize)

    @unittest2.skipIf(sys.version_info.major == 2, 'specific to Python 3')
    def test_path_type_numeric_union_good_7_py3(self):
        """An int, float should accept variety of numeric types."""
        self._rule_path_type_good((int, float), '42.2', 42.2)

    @unittest2.skipIf(sys.version_info.major == 2, 'specific to Python 3')
    def test_path_type_numeric_union_good_8_py3(self):
        """An int, float should accept variety of numeric types."""
        self._rule_path_type_good((int, float), '1.e+5', 100000)

    @unittest2.skipIf(sys.version_info.major == 2, 'specific to Python 3')
    def test_path_type_numeric_union_good_9_py3(self):
        """An int, float should accept variety of numeric types."""
        self._rule_path_type_good((int, float), '.inf', float('inf'))

    @unittest2.skipIf(sys.version_info.major == 2, 'specific to Python 3')
    def test_path_type_numeric_union_good_10_py3(self):
        """An int, float should accept variety of numeric types."""
        self._rule_path_type_good((int, float), '-.inf', -float('inf'))

    @unittest2.skipIf(sys.version_info.major == 2, 'specific to Python 3')
    def test_path_type_numeric_union_good_11_py3(self):
        """int, float should accept variety of numeric types."""
        self._rule_path_type_good(
            (int, float), '.nan', 'nan', normalizer=str)

    @unittest2.skipIf(sys.version_info.major == 2, 'specific to Python 3')
    def test_path_type_numeric_union_good_12_py3(self):
        """int, float should accept variety of numeric types."""
        self._rule_path_type_good(
            (int, float), str(sys.maxsize+1), sys.maxsize+1)

    @unittest2.skipIf(sys.version_info.major == 2, 'specific to Python 3')
    def test_path_type_numeric_union_bad_py3(self):
        """Test that int, float rejects string."""
        # pylint: disable=undefined-variable
        self._rule_path_type_bad(
            (int, float), 'forty-two', 'has type str not type int or float')


class PathTypeTestTimestamps(TestCase):
    """Test that path_type recognizes dates and datetimes."""

    def test_path_type_datetime_good(self):
        """A datetime should recognize valid datetimes."""
        self._rule_path_type_good(
            datetime, '2020-01-01 02:03:04', datetime(2020, 1, 1, 2, 3, 4))

    def test_path_type_datetime_union_good_1(self):
        """A date, datetime union should recognizes dates and datetimes."""
        self._rule_path_type_good(
            (date, datetime), '2020-01-01',
            date(2020, 1, 1))

    def test_path_type_datetime_union_good_2(self):
        """A date, datetime union should recognizes dates and datetimes."""
        self._rule_path_type_good(
            (date, datetime), '2020-01-01 02:03:04',
            datetime(2020, 1, 1, 2, 3, 4))

    def test_path_type_date_for_datetime_good(self):
        """A date should recognizes datetimes due to inheritance."""
        datetimevalue = datetime(2020, 1, 1, 2, 3, 4)
        self.assertIsInstance(datetimevalue, date)

    def test_path_type_date_good_1(self):
        """A date should recognize valid dates and datetimes."""
        self._rule_path_type_good(date, '2020-01-01', date(2020, 1, 1))

    def test_path_type_date_good_2(self):
        """A date should recognize valid dates and datetimes."""
        self._rule_path_type_good(
            date, '2020-01-01 02:03:04', datetime(2020, 1, 1, 2, 3, 4))

    def test_path_type_date_good_3(self):
        """A date should recognize valid dates and datetimes."""
        self._rule_path_type_good(
            date, '2020-01-01 02:03:04Z', datetime(2020, 1, 1, 2, 3, 4),
            normalizer=_as_naive_datetime_in_utc)

    def test_path_type_date_good_4(self):
        """A date should recognize valid dates and datetimes."""
        self._rule_path_type_good(date, '1995-02-04', date(1995, 2, 4))

    def test_path_type_date_good_5(self):
        """A date should recognize valid dates and datetimes."""
        self._rule_path_type_good(
            date, '2020-01-02 00:00:00', datetime(2020, 1, 2, 0, 0, 0))

    def test_path_type_date_good_6(self):
        """A date should recognize valid dates and datetimes."""
        self._rule_path_type_good(
            date, '2020-01-01 02:03:04+11',
            datetime(2019, 12, 31, 15, 3, 4),
            normalizer=_as_naive_datetime_in_utc)

    def test_path_type_date_good_7(self):
        """A date should recognize valid dates and datetimes."""
        self._rule_path_type_good(
            date, '2020-01-01 02:03:04-11',
            datetime(2020, 1, 1, 13, 3, 4),
            normalizer=_as_naive_datetime_in_utc)

    def test_path_type_date_good_8(self):
        """A date should recognize valid dates and datetimes."""
        self._rule_path_type_good(
            date, '2020-01-01 02:03:04+11:00',
            datetime(2019, 12, 31, 15, 3, 4),
            normalizer=_as_naive_datetime_in_utc)

    def test_path_type_date_good_9(self):
        """A date should recognize valid dates and datetimes."""
        self._rule_path_type_good(
            date, '2020-01-01 02:03:04.321+11',
            datetime(2019, 12, 31, 15, 3, 4, 321000),
            normalizer=_as_naive_datetime_in_utc)

    def test_path_type_date_good_10(self):
        """A date should recognize valid dates and datetimes."""
        self._rule_path_type_good(
            date, '2020-01-01 02:03:04.321987+11',
            datetime(2019, 12, 31, 15, 3, 4, 321987),
            normalizer=_as_naive_datetime_in_utc)

    def test_path_type_date_good_11(self):
        """A date should recognize valid dates and datetimes."""
        self._rule_path_type_good(
            date, '1996-12-19T16:39:57-08:00',
            datetime(1996, 12, 20, 0, 39, 57),
            normalizer=_as_naive_datetime_in_utc)

    def test_path_type_date_bad_1(self):
        """A datetime should reject dates (but not vice-versa)."""
        self._rule_path_type_bad(
            datetime, '2020-01-01', 'has type date not type datetime')

    def test_path_type_date_bad_2(self):
        """A date should reject dates with no hyphen separators."""
        self._rule_path_type_bad(
            date, '20200101', 'has type int not type date')

    def test_path_type_date_bad_3(self):
        """A date should reject dates with only year and month."""
        self._rule_path_type_bad(date, '2020-01', 'has type str not type date')

    def test_path_type_date_bad_4(self):
        """A date should reject times without dates."""
        self._rule_path_type_bad(date, '02:03:04', 'has type str not type date')

    def test_path_type_date_bad_5(self):
        """A date should reject datetimes with no seconds."""
        self._rule_path_type_bad(
            date, '2020-01-01 02:03', 'has type str not type date')

    def test_path_type_date_bad_6(self):
        """A datetime rejects datetimes expressing 24:00 end-of-day."""
        # This is less a test of proper behavior and more a canary check
        # of actual behavior.  While the YAML parser recognizes the
        # value as a timestamp, the datetime constructor that it invokes
        # generates an exception.
        self._rule_path_type_bad(
            date, '2020-01-01 24:00:00', r'hour must be in 0\.\.23')


class PathTypeTestMapsAndLists(TestCase):
    """Test that path_type recognizes map and list structures."""

    def test_path_type_dict_on_root_map_good(self):
        """A root map should be recognized as dict."""
        self._write_file(self.conffile, """
        aaa: aaaaa
        bbb: bbbbb
        """)
        confp = YamlConfigParser(path_type=dict)
        confp.add_rule('*')
        conf = confp.parse_file(self.conffile)
        self.assertIsInstance(conf, YamlConfig)
        self.assertEqual(conf.aaa, 'aaaaa')
        self.assertEqual(conf.bbb, 'bbbbb')

    def test_path_type_dict_on_root_list_bad(self):
        """A root list should be rejected as dict."""
        self._write_file(self.conffile, """
        - aaaaa
        - bbbbb
        """)
        confp = YamlConfigParser(path_type=dict)
        confp.add_rule('*')
        with self.assertRaisesRegex(
                ParseError, r'\*root\* has type list not type dict'):
            confp.parse_file(self.conffile)

    def test_path_type_list_on_root_list_good(self):
        """A root list should be recognized as list."""
        self._write_file(self.conffile, """
        - aaaaa
        - bbbbb
        """)
        confp = YamlConfigParser(path_type=list)
        confp.add_rule('*')
        conf = confp.parse_file(self.conffile)
        self.assertIsInstance(conf, YamlConfigList)
        self.assertEqual(conf[0], 'aaaaa')
        self.assertEqual(conf[1], 'bbbbb')

    def test_path_type_list_on_root_map_bad(self):
        """A root map should be rejected as list."""
        self._write_file(self.conffile, """
        aaa: aaaaa
        bbb: bbbbb
        """)
        confp = YamlConfigParser(path_type=list)
        confp.add_rule('*')
        with self.assertRaisesRegex(
                ParseError, r'\*root\* has type dict not type list'):
            confp.parse_file(self.conffile)

    def test_path_type_dict_on_path_map_good(self):
        """A map on path should be recognized as dict."""
        self._write_file(self.conffile, """
        field:
          aaa: aaaaa
          bbb: bbbbb
        """)
        confp = YamlConfigParser()
        confp.add_rule('field', path_type=dict)
        confp.add_rule('field.*')
        conf = confp.parse_file(self.conffile)
        self.assertIsInstance(conf.field, YamlConfig)
        self.assertEqual(conf.field.aaa, 'aaaaa')
        self.assertEqual(conf.field.bbb, 'bbbbb')

    def test_path_type_dict_on_path_list_bad(self):
        """A list on path should be rejected as dict."""
        self._write_file(self.conffile, """
        field:
        - aaaaa
        - bbbbb
        """)
        confp = YamlConfigParser()
        confp.add_rule('field', path_type=dict)
        confp.add_rule('field.*')
        with self.assertRaisesRegex(
                ParseError, '"field" has type list not type dict'):
            confp.parse_file(self.conffile)

    def test_path_type_list_on_path_list_good(self):
        """A list on path should be recognized as list."""
        self._write_file(self.conffile, """
        field:
        - aaaaa
        - bbbbb
        """)
        confp = YamlConfigParser()
        confp.add_rule('field', path_type=list)
        confp.add_rule('field.*')
        conf = confp.parse_file(self.conffile)
        self.assertIsInstance(conf.field, YamlConfigList)
        self.assertEqual(conf.field[0], 'aaaaa')
        self.assertEqual(conf.field[1], 'bbbbb')

    def test_path_type_list_on_path_dict_bad(self):
        """A map on path should be rejected as list."""
        self._write_file(self.conffile, """
        field:
          aaa: aaaaa
          bbb: bbbbb
        """)
        confp = YamlConfigParser()
        confp.add_rule('field', path_type=list)
        confp.add_rule('field.*')
        with self.assertRaisesRegex(
                ParseError, '"field" has type dict not type list'):
            confp.parse_file(self.conffile)


class RuleTestBasics(TestCase):
    """Test the basic functionality of the rule tests."""

    def test_rule_test_basics_success(self):
        """Test that a test that returns None succeeds."""
        # pylint: disable=unused-argument, missing-docstring
        def is_success(conf, path, value):
            return None
        self._rule_test_good(is_success, 'aaaaa')

    def test_rule_test_basics_failure(self):
        """Test that a test that returns a string fails."""
        # pylint: disable=unused-argument, missing-docstring
        def is_failure(conf, path, value):
            return 'a detailed explanation of why'
        self._rule_test_bad(
            is_failure, 'aaaaa', 'failed test: a detailed explanation of why')

    def test_rule_test_basics_error(self):
        """Test that test raising an error fails with explanation."""
        # pylint: disable=unused-argument, missing-docstring
        def is_error(conf, path, value):
            raise RuntimeError('what went wrong')
        self._rule_test_bad(
            is_error, 'aaaaa', 'test raised exception: what went wrong')


class RuleTestIsRegex(TestCase):
    """Test the functionality of the is_regex rule test."""

    def test_rule_test_regex_good_1(self):
        """Test test_regex recognizes an entire value matching the pattern."""
        self._rule_test_good(test.is_regex('[a-z]{5}'), 'aaaaa')

    def test_rule_test_regex_good_2(self):
        """Test test_regex recognizes a value containing the pattern."""
        self._rule_test_good(test.is_regex('[a-z]{5}'), 'XaaaaaX')

    def test_rule_test_regex_good_3(self):
        """Test test_regex recognizes a value containing the pattern."""
        self._rule_test_good(test.is_regex('[a-z]{5}'), u'ØaaaaaØ')

    def test_rule_test_regex_good_4(self):
        """Test test_regex invert recognizes a value not matching pattern."""
        self._rule_test_good(test.is_regex('[a-z]{5}', invert=True), u'aaaa')

    def test_rule_test_regex_good_5(self):
        """Test test_regex invert recognizes a value not matching pattern."""
        self._rule_test_good(test.is_regex('[a-z]{5}', invert=True), u'AAAAAA')

    def test_rule_test_regex_good_6(self):
        """Test test_regex invert recognizes a value not matching pattern."""
        self._rule_test_good(
            test.is_regex('^[a-z]{5}$', invert=True), u'cccccc')

    def test_rule_test_regex_good_7(self):
        """Test test_regex recognizes a value matching a unicode pattern."""
        self._rule_test_good(test.is_regex(u'Ø{5}'), u'xØØØØØx')

    def test_rule_test_regex_bad_1(self):
        """Test test_regex rejects a value not matching the pattern."""
        self._rule_test_bad(
            test.is_regex('[a-z]{5}'), 'AAAAA',
            r'"AAAAA" does not match /\[a-z\]\{5\}/')

    def test_rule_test_regex_bad_2(self):
        """Test test_regex rejects a value not matching anchored pattern."""
        self._rule_test_bad(
            test.is_regex('^[a-z]{5}$'), 'XaaaaaX', 'does not match')

    def test_rule_test_regex_bad_3(self):
        """Test test_regex errors on an integer value."""
        self._rule_test_bad(
            test.is_regex('^[a-z]{5}$'), 42, 'test raised exception')

    def test_rule_test_regex_bad_4(self):
        """Test test_regex invert rejects a value matching the pattern."""
        self._rule_test_bad(
            test.is_regex('[a-z]{5}', invert=True), 'aaaaa',
            r'"aaaaa" matches /\[a-z\]\{5\}/')

    def test_rule_test_regex_bad_5(self):
        """Test test_regex rejects a value not matching unicode pattern."""
        # Suppress the pattern-matching of the exception since the
        # unittest code has an explicit str in it that raises a
        # UnicodeEncodeError.  So, just confirm the exception, not that
        # it contains the pattern:
        #    u'"aaaaa" does not match /Ø\{5\}/')
        self._rule_test_bad(test.is_regex(u'Ø{5}'), 'aaaaa', excrex=None)

    def test_rule_test_regex_config_error_1(self):
        """Test bad test_regex regex fails during parser config."""
        confp = YamlConfigParser()
        with self.assertRaises(sre_constants.error):
            confp.add_rule('field', test=test.is_regex('[unclosed'))


class RuleTestIsInterval(TestCase):
    """Test the functionality of the is_interval rule test."""

    def test_rule_test_interval_good_1(self):
        """Test test_interval recognizes a value within the interval."""
        self._rule_test_good(test.is_interval(50, 100), '50', testvalue=50)

    def test_rule_test_interval_good_2(self):
        """Test test_interval recognizes a value within the interval."""
        self._rule_test_good(test.is_interval(50, 100), '99', testvalue=99)

    def test_rule_test_interval_good_3(self):
        """Test test_interval recognizes a value within the interval."""
        self._rule_test_good(
            test.is_interval(50, 100, include_upper=True), '100', testvalue=100)

    def test_rule_test_interval_good_4(self):
        """Test test_interval recognizes a value within the interval."""
        self._rule_test_good(test.is_interval(50, 100), '50.0', testvalue=50.0)

    def test_rule_test_interval_good_5(self):
        """Test test_interval recognizes a value within the interval."""
        self._rule_test_good(
            test.is_interval(50, 100), '5.e+1', testvalue=5.e+1)

    def test_rule_test_interval_good_6(self):
        """Test test_interval recognizes a value within the interval."""
        self._rule_test_good(
            test.is_interval(50, 100), '9.9999e+1', testvalue=99.999)

    def test_rule_test_interval_good_7(self):
        """Test test_interval recognizes a single-value interval."""
        self._rule_test_good(
            test.is_interval(50, 50, include_upper=True), '50', testvalue=50)

    def test_rule_test_interval_good_8(self):
        """Test test_interval recognizes a single-value interval."""
        self._rule_test_good(
            test.is_interval(50, 50, include_upper=True), '50.0',
            testvalue=50.0)

    def test_rule_test_interval_good_9(self):
        """Test test_interval recognizes valid intervals on strings."""
        self._rule_test_good(test.is_interval('a', 'n'), 'a')

    def test_rule_test_interval_good_10(self):
        """Test test_interval recognizes valid intervals on strings."""
        self._rule_test_good(test.is_interval('a', 'n'), 'm')

    def test_rule_test_interval_good_11(self):
        """Test test_interval recognizes valid intervals on strings."""
        self._rule_test_good(test.is_interval('a', 'n'), 'mzzzzzzzz')

    def test_rule_test_interval_good_12(self):
        """Test test_interval recognizes valid intervals on strings."""
        self._rule_test_good(
            test.is_interval('a', 'n', include_upper=True), 'n')

    def test_rule_test_interval_bad_1(self):
        """Test test_interval rejects upper-bound value by default."""
        self._rule_test_bad(
            test.is_interval(50, 100), '100',
            r'is above the interval \[50, 100\)')

    def test_rule_test_interval_bad_2(self):
        """Test test_interval rejects excluded lower-bound value."""
        self._rule_test_bad(
            test.is_interval(50, 100, exclude_lower=True), '50.0',
            r'is below the interval \(50, 100\)')

    def test_rule_test_interval_bad_3(self):
        """Test test_interval rejects upper-bound value on strings."""
        self._rule_test_bad(
            test.is_interval('a', 'n'), 'n',
            r'is above the interval \[\'a\', \'n\'\)')

    def test_rule_test_interval_bad_4(self):
        """Test bad test_interval fails during parser config."""
        self._rule_test_bad(
            test.is_interval('a', 'n', include_upper=True), 'na',
            r'is above the interval \[\'a\', \'n\'\]')

    def test_rule_test_interval_config_error_1(self):
        """Test bad test_interval fails during parser config."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(Exception, 'invalid interval'):
            confp.add_rule('field', test=test.is_interval(100, 50))

    def test_rule_test_interval_config_error_2(self):
        """Test bad test_interval fails during parser config."""
        confp = YamlConfigParser()
        with self.assertRaisesRegex(Exception, 'invalid interval'):
            confp.add_rule('field', test=test.is_interval(50, 50))


class RuleTestIsIPv4AddressTests(TestCase):
    """Test the functionality of the is_ipv4_address rule test."""

    def test_rule_test_is_ipv4_address_good_1(self):
        """Test is_ipv4_address recognizes a valid IPv4 address."""
        self._rule_test_good(test.is_ipv4_address, '127.0.0.1')

    def test_rule_test_is_ipv4_address_good_2(self):
        """Test is_ipv4_address recognizes a valid IPv4 address."""
        self._rule_test_good(test.is_ipv4_address, '0.0.0.0')

    def test_rule_test_is_ipv4_address_good_3(self):
        """Test is_ipv4_address recognizes a valid IPv4 address."""
        self._rule_test_good(test.is_ipv4_address, '255.255.255.255')

    def test_rule_test_is_ipv4_address_good_4(self):
        """Test is_ipv4_address recognizes a valid IPv4 address."""
        self._rule_test_good(test.is_ipv4_address, '192.168.0.1')

    def test_rule_test_is_ipv4_address_good_5(self):
        """Test is_ipv4_address recognizes a valid IPv4 address."""
        self._rule_test_good(test.is_ipv4_address, '8.8.8.8')

    def test_rule_test_is_ipv4_address_good_6(self):
        """Test is_ipv4_address recognizes a valid IPv4 address."""
        self._rule_test_good(test.is_ipv4_address, '1.1.1.1')

    def test_rule_test_is_ipv4_address_bad_1(self):
        """Test is_ipv4_address rejects non-dotted-quad notation."""
        self._rule_test_bad(
            test.is_ipv4_address, 'example.com',
            'must be in IPv4 dotted-quad notation')

    def test_rule_test_is_ipv4_address_bad_2(self):
        """Test is_ipv4_address rejects non-dotted-quad notation."""
        self._rule_test_bad(
            test.is_ipv4_address, '3232235521',
            '3232235521 must be a string in IPv4 dotted-quad notation')

    def test_rule_test_is_ipv4_address_bad_3(self):
        """Test is_ipv4_address rejects non-dotted-quad notation."""
        self._rule_test_bad(
            test.is_ipv4_address, '127.0.0.0.1',
            'must be in IPv4 dotted-quad notation')

    def test_rule_test_is_ipv4_address_bad_4(self):
        """Test is_ipv4_address rejects non-dotted-quad notation."""
        self._rule_test_bad(
            test.is_ipv4_address, '192.168.555.1',
            '3rd octet of "192.168.555.1" exceeds 255')


class RuleTestIsDomainNameTests(TestCase):
    """Test the functionality of the is_domain_name rule test."""

    def test_rule_test_is_domain_name_good_1(self):
        """Test is_domain_name recognizes a valid domain name."""
        self._rule_test_good(test.is_domain_name, 'example.com')

    def test_rule_test_is_domain_name_good_2(self):
        """Test is_domain_name recognizes a valid domain name."""
        self._rule_test_good(test.is_domain_name, 'mail.hr.example.com')

    def test_rule_test_is_domain_name_good_3(self):
        """Test is_domain_name recognizes a valid domain name."""
        self._rule_test_good(test.is_domain_name, 'www.h-y-p-h-e-n.example.com')

    def test_rule_test_is_domain_name_good_4(self):
        """Test is_domain_name recognizes a valid domain name."""
        domname = '1.'+'.'.join(['0'] * 31)+'.ip6.arpa'
        self._rule_test_good(test.is_domain_name, domname)

    def test_rule_test_is_domain_name_bad_1(self):
        """Test is_domain_name rejects an FQDN with a trailing dot."""
        self._rule_test_bad(
            test.is_domain_name, 'www.example.com.',
            'cannot have an empty label')

    def test_rule_test_is_domain_name_bad_2(self):
        """Test is_domain_name rejects domain labels with leading hyphens."""
        self._rule_test_bad(
            test.is_domain_name, 'www.-hr.example.com"',
            'label cannot start or end with "-"')

    def test_rule_test_is_domain_name_bad_3(self):
        """Test is_domain_name rejects domain labels with trailing hyphens."""
        self._rule_test_bad(
            test.is_domain_name, 'www.hr-.example.com"',
            'label cannot start or end with "-"')

    def test_rule_test_is_domain_name_bad_4(self):
        """Test is_domain_name rejects excessive number of labels."""
        domname = '.'.join(['a'] * 126)+'.example.com'
        self._rule_test_bad(
            test.is_domain_name, domname, 'cannot have more than 127 labels')

    def test_rule_test_is_domain_name_bad_5(self):
        """Test is_domain_name rejects excessively large label."""
        domname = 'www.'+'a'*63+'.example.com'
        self._rule_test_bad(
            test.is_domain_name, domname, r'cannot have a 63\+ byte label')

    def test_rule_test_is_domain_name_bad_6(self):
        """Test is_domain_name rejects numeric TLD as invalid."""
        self._rule_test_bad(
            test.is_domain_name, 'www.example.321',
            'top-level domain cannot be only digits')

    def test_rule_test_is_domain_name_bad_7(self):
        """Test is_domain_name rejects empty label."""
        self._rule_test_bad(
            test.is_domain_name, 'www..example.com"',
            'cannot have an empty label')

    def test_rule_test_is_domain_name_bad_8(self):
        """Test is_domain_name rejects empty domain."""
        self._rule_test_bad(
            test.is_domain_name, '', 'cannot be empty')

    def test_rule_test_is_domain_name_bad_9(self):
        """Test is_domain_name rejects empty domain."""
        self._rule_test_bad(
            test.is_domain_name, '', 'cannot be empty', quoted=True)


class RuleTestIsEmailAddressTests(TestCase):
    """Test the functionality of the is_email_address rule test."""

    def test_rule_test_is_email_address_good_1(self):
        """Test is_email_address recognizes a valid email address address."""
        self._rule_test_good(test.is_email_address, 'user@example.com')

    def test_rule_test_is_email_address_good_2(self):
        """Test is_email_address recognizes a valid email address address."""
        self._rule_test_good(
            test.is_email_address, r'"Abc:def"@example.com', quoted=True)

    def test_rule_test_is_email_address_good_3(self):
        """Test is_email_address recognizes a valid email address address."""
        self._rule_test_good(
            test.is_email_address, '"Abc@def"@example.com', quoted=True)

    def test_rule_test_is_email_address_good_4(self):
        """Test is_email_address recognizes a valid email address address."""
        self._rule_test_good(
            test.is_email_address, 'customer/department=shipping@example.com')

    def test_rule_test_is_email_address_good_5(self):
        """Test is_email_address recognizes a valid email address address."""
        self._rule_test_good(
            test.is_email_address, '!def!xyz%abc@example.com', quoted=True)

    def test_rule_test_is_email_address_good_6(self):
        """Test is_email_address recognizes a valid email address address."""
        self._rule_test_good(
            test.is_email_address, '"Joe Blow"@example.com', quoted=True)

    def test_rule_test_is_email_address_good_7(self):
        """Test is_email_address recognizes a valid email address address."""
        self._rule_test_good(
            test.is_email_address, '".John.Doe."@example.com', quoted=True)

    def test_rule_test_is_email_address_good_8(self):
        """Test is_email_address recognizes a valid email address address."""
        self._rule_test_good(
            test.is_email_address, '"John..Doe"@example.com', quoted=True)

    def test_rule_test_is_email_address_good_9(self):
        """Test is_email_address recognizes a valid email address address."""
        self._rule_test_good(test.is_email_address, 'fred+foo@example.com')

    def test_rule_test_is_email_address_good_10(self):
        """Test is_email_address recognizes a valid email address address."""
        self._rule_test_good(test.is_email_address, 'fred+bar@example.com')

    def test_rule_test_is_email_address_good_11(self):
        """Test is_email_address recognizes a valid email address address."""
        self._rule_test_good(test.is_email_address, 'fred-foo@example.com')

    def test_rule_test_is_email_address_good_12(self):
        """Test is_email_address recognizes a valid email address address."""
        self._rule_test_good(
            test.is_email_address, '" "@example.com', quoted=True)

    def test_rule_test_is_email_address_bad_1(self):
        """Test is_email_address rejects missing user and domain parts."""
        self._rule_test_bad(
            test.is_email_address, 'username-AT-domain',
            'is not of the form username@domain')

    def test_rule_test_is_email_address_bad_2(self):
        """Test is_email_address rejects domain literals."""
        self._rule_test_bad(
            test.is_email_address, 'username@[127.0.0.1]',
            r'cannot contain "\["')

    def test_rule_test_is_email_address_bad_3(self):
        """Test is_email_address rejects empty userpart."""
        self._rule_test_bad(
            test.is_email_address, '@example.com',
            'has empty userpart', quoted=True)

    def test_rule_test_is_email_address_bad_4(self):
        """Test is_email_address rejects null email."""
        self._rule_test_bad(
            test.is_email_address, '', 'cannot be empty')

    def test_rule_test_is_email_address_bad_5(self):
        """Test is_email_address rejects empty email."""
        self._rule_test_bad(
            test.is_email_address, '', 'cannot be empty', quoted=True)

    def test_rule_test_is_email_address_bad_6(self):
        """Test is_email_address rejects long userpart."""
        self._rule_test_bad(
            test.is_email_address,
            '{0}@example.com'.format('a' * 64),
            r'has 64\+ byte userpart')

    def test_rule_test_is_email_address_bad_7(self):
        """Test is_email_address rejects invalid userpart."""
        self._rule_test_bad(
            test.is_email_address, 'Abc:def@example.com',
            'unquoted userpart cannot contain', quoted=True)

    def test_rule_test_is_email_address_bad_8(self):
        """Test is_email_address rejects invalid userpart."""
        self._rule_test_bad(
            test.is_email_address, '.username@example.com',
            'unquoted userpart cannot start or end with')

    def test_rule_test_is_email_address_bad_9(self):
        """Test is_email_address rejects invalid userpart."""
        self._rule_test_bad(
            test.is_email_address, 'username.@example.com',
            'unquoted userpart cannot start or end with')

    def test_rule_test_is_email_address_bad_10(self):
        """Test is_email_address rejects invalid userpart."""
        self._rule_test_bad(
            test.is_email_address, 'user..name@example.com',
            r'unquoted userpart cannot contain "\.\."')

    def test_rule_test_is_email_address_bad_11(self):
        """Test is_email_address rejects invalid userpart."""
        self._rule_test_bad(
            test.is_email_address, '"Abc\\def"@example.com',
            'userpart quoted content cannot contain', quoted=True)

    def test_rule_test_is_email_address_bad_12(self):
        """Test is_email_address rejects empty domain part."""
        self._rule_test_bad(
            test.is_email_address, 'username@',
            'has empty domainpart', quoted=True)

    def test_rule_test_is_email_address_bad_13(self):
        """Test is_email_address rejects invalid userpart."""
        self._rule_test_bad(
            test.is_email_address,
            'username@{0}.example.com'.format('a' * (63 - len('.example.com'))),
            r'has 63\+ byte domainpart', quoted=True)


class RuleTestIsUrlTests(TestCase):
    """Test the functionality of the is_url rule test."""

    def test_rule_test_is_url_good_1(self):
        """Test is_url recognizes a valid url."""
        self._rule_test_good(
            test.is_url, 'http://foo.com/blah_blah', quoted=True)

    def test_rule_test_is_url_good_2(self):
        """Test is_url recognizes a valid url."""
        self._rule_test_good(
            test.is_url, 'https://www.w3.org/TR/xml/#dt-content', quoted=True)

    def test_rule_test_is_url_good_3(self):
        """Test is_url recognizes a valid url."""
        self._rule_test_good(
            test.is_url, 'http://1337.net', quoted=True)

    def test_rule_test_is_url_good_4(self):
        """Test is_url recognizes a valid url."""
        self._rule_test_good(
            test.is_url, 'http://142.42.1.1:8080/', quoted=True)

    def test_rule_test_is_url_good_5(self):
        """Test is_url recognizes a valid url."""
        self._rule_test_good(
            test.is_url, 'http://userid:password@example.com:8080/',
            quoted=True)

    def test_rule_test_is_url_good_6(self):
        """Test is_url recognizes a valid url."""
        self._rule_test_good(
            test.is_url, 'https://www.example.com/foo/?bar=baz&inga=42&quux',
            quoted=True)

    def test_rule_test_is_url_good_7(self):
        """Test is_url recognizes a valid url."""
        self._rule_test_good(
            test.is_url, 'http://foo.bar/?q=Test%20URL-encoded%20stuff',
            quoted=True)

    def test_rule_test_is_url_good_8(self):
        """Test is_url recognizes a valid url."""
        self._rule_test_good(
            test.is_url, 'https://code.google.com/events/#&product=browser',
            quoted=True)

    def test_rule_test_is_url_good_9(self):
        """Test is_url recognizes a valid url."""
        self._rule_test_good(
            test.is_url, 'http://xn--bcher-kva.tld', quoted=True)

    def test_rule_test_is_url_bad_1(self):
        """Test is_url rejects unencoded spaces."""
        self._rule_test_bad(
            test.is_url, 'http://foo.bar?q=Spaces should be encoded',
            'not recognized as a valid url', quoted=True)

    def test_rule_test_is_url_bad_2(self):
        """Test is_url rejects urls with parentheses.

        Apparently they should be valid, and are used by sites like
        Wikipedia, but since it currently fails, this test exists to
        document the behavior for regression testing purposes and
        possible removal.

        """
        self._rule_test_bad(
            test.is_url, 'http://foo.com/blah_blah_(wikipedia)_(again)',
            'not recognized as a valid url', quoted=True)

    def test_rule_test_is_url_bad_3(self):
        """Test is_url rejects missing scheme."""
        self._rule_test_bad(
            test.is_url, '://example.com',
            'not recognized as a valid url', quoted=True)

    def test_rule_test_is_url_bad_4(self):
        """Test is_url rejects missing domain."""
        self._rule_test_bad(
            test.is_url, 'http:///index.html',
            'not recognized as a valid url', quoted=True)

    def test_rule_test_is_url_bad_5(self):
        """Test is_url rejects missing separator."""
        self._rule_test_bad(
            test.is_url, 'http:/example.com',
            'not recognized as a valid url', quoted=True)

    def test_rule_test_is_url_bad_6(self):
        """Test is_url rejects null url."""
        self._rule_test_bad(
            test.is_url, '', 'cannot be empty')

    def test_rule_test_is_url_bad_7(self):
        """Test is_url rejects empty."""
        self._rule_test_bad(
            test.is_url, '', 'cannot be empty', quoted=True)


class RuleTestIsFilePathTests(TestCase):
    """Test the functionality of the test_path rule tests."""

    # Tests of 'exists'
    def test_rule_test_path_exists_on_file(self):
        """Test exists succeeds when file exists."""
        filepath = '{0}_existing_file.txt'.format(self.testname)
        self._write_file(self.conffile, 'field: {0}'.format(filepath))
        self._write_file(filepath, 'test file')
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('exists'))
        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.field, filepath)

    def test_rule_test_path_exists_on_dir(self):
        """Test exists succeeds when dir exists."""
        dirpath = '{0}_existing_dir'.format(self.testname)
        self._write_file(self.conffile, 'field: {0}'.format(dirpath))
        os.mkdir(dirpath)
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('exists'))
        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.field, dirpath)

    def test_rule_test_path_exists_on_path(self):
        """Test exists succeeds when path exists."""
        dirpath = '{0}_existing_dir'.format(self.testname)
        filepath = os.path.join(dirpath, 'test_file.txt')
        self._write_file(self.conffile, """
        dirpath: {0}
        filepath: {1}
        """.format(dirpath, filepath))
        os.mkdir(dirpath)
        self._write_file(filepath, 'test file contents')
        confp = YamlConfigParser()
        confp.add_rule('dirpath', test=test.is_file_path('exists'))
        confp.add_rule('filepath', test=test.is_file_path('exists'))
        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.dirpath, dirpath)
        self.assertEqual(conf.filepath, filepath)

    def test_rule_test_path_exists_missing(self):
        """Test exists fails when path does not exist."""
        self._write_file(self.conffile, 'field: does_not_exist')
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('exists'))
        with self.assertRaisesRegex(
                ParseError, '"does_not_exist" does not exist'):
            confp.parse_file(self.conffile)

    # Tests of '!exists'
    def test_rule_test_path_not_exists_on_file(self):
        """Test !exists fails when file exists."""
        filepath = '{0}_existing_file.txt'.format(self.testname)
        self._write_file(self.conffile, 'field: {0}'.format(filepath))
        self._write_file(filepath, 'test file')
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('!exists'))
        with self.assertRaisesRegex(
                ParseError, '"{0}" exists'.format(filepath)):
            confp.parse_file(self.conffile)

    def test_rule_test_path_not_exists_missing(self):
        """Test !exists succeeds when path does not exist."""
        self._write_file(self.conffile, 'field: does_not_exist')
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('!exists'))
        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.field, 'does_not_exist')

    # Tests of 'isdir'
    def test_rule_test_path_isdir_on_dir(self):
        """Test isdir succeeds when dir exists."""
        dirpath = '{0}_existing_dir'.format(self.testname)
        self._write_file(self.conffile, 'field: {0}'.format(dirpath))
        os.mkdir(dirpath)
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('isdir'))
        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.field, dirpath)

    def test_rule_test_path_isdir_on_file(self):
        """Test isdir fails when file exists."""
        filepath = '{0}_existing_file.txt'.format(self.testname)
        self._write_file(self.conffile, 'field: {0}'.format(filepath))
        self._write_file(filepath, 'test file')
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('isdir'))
        with self.assertRaisesRegex(
                ParseError, '"{0}" is not a directory'.format(filepath)):
            confp.parse_file(self.conffile)

    def test_rule_test_path_isdir_missing(self):
        """Test isdir fails (with unhelpful error) when path is missing."""
        self._write_file(self.conffile, 'field: does_not_exist')
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('isdir'))
        with self.assertRaisesRegex(
                ParseError, '"does_not_exist" is not a directory'):
            confp.parse_file(self.conffile)

    # Tests of '!isdir'
    def test_rule_test_path_not_isdir_missing(self):
        """Test !isdir succeeds when path is missing."""
        missingpath = 'does_not_exist'
        self._write_file(self.conffile, 'field: {0}'.format(missingpath))
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('!isdir'))
        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.field, missingpath)

    def test_rule_test_path_not_isdir_on_dir(self):
        """Test !isdir fails when path is dir."""
        dirpath = '{0}_existing_dir'.format(self.testname)
        self._write_file(self.conffile, 'field: {0}'.format(dirpath))
        os.mkdir(dirpath)
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('!isdir'))
        with self.assertRaisesRegex(
                ParseError, '"{0}" is a directory'.format(dirpath)):
            _ = confp.parse_file(self.conffile)

    # Tests of 'isfile'
    def test_rule_test_path_isfile_on_file(self):
        """Test isfile succeeds when file exists."""
        filepath = '{0}_existing_file.txt'.format(self.testname)
        self._write_file(self.conffile, 'field: {0}'.format(filepath))
        self._write_file(filepath, 'test file')
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('isfile'))
        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.field, filepath)

    def test_rule_test_path_isfile_on_dir(self):
        """Test isfile fails when dir exists."""
        dirpath = '{0}_existing_dir'.format(self.testname)
        self._write_file(self.conffile, 'field: {0}'.format(dirpath))
        os.mkdir(dirpath)
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('isfile'))
        with self.assertRaisesRegex(
                ParseError, '"{0}" is not a file'.format(dirpath)):
            confp.parse_file(self.conffile)

    def test_rule_test_path_isfile_missing(self):
        """Test isfile fails (with unhelpful error) when path is missing."""
        self._write_file(self.conffile, 'field: does_not_exist')
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('isfile'))
        with self.assertRaisesRegex(
                ParseError, '"does_not_exist" is not a file'):
            confp.parse_file(self.conffile)

    # Tests of '!isfile'
    def test_rule_test_path_not_isfile_missing(self):
        """Test !isfile succeeds when path is missing."""
        missingpath = 'does_not_exist'
        self._write_file(self.conffile, 'field: {0}'.format(missingpath))
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('!isfile'))
        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.field, missingpath)

    def test_rule_test_path_not_isfile_on_file(self):
        """Test !isfile fails when path is file."""
        filepath = '{0}_existing_file.txt'.format(self.testname)
        self._write_file(self.conffile, 'field: {0}'.format(filepath))
        self._write_file(filepath, 'test file')
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('!isfile'))
        with self.assertRaisesRegex(
                ParseError, '"{0}" is a file'.format(filepath)):
            _ = confp.parse_file(self.conffile)

    # Tests of 'islink'
    @unittest2.skipUnless(sys.platform.startswith('linux'), 'requires linux')
    def test_rule_test_path_islink_on_link(self):
        """Test islink succeeds when path is a link."""
        filepath = '{0}_existing_file.txt'.format(self.testname)
        linkpath = '{0}_existing_link.txt'.format(self.testname)
        self._write_file(self.conffile, 'field: {0}'.format(linkpath))
        self._write_file(filepath, 'test file')
        os.symlink(filepath, linkpath)
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('islink'))
        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.field, linkpath)

    @unittest2.skipUnless(sys.platform.startswith('linux'), 'requires linux')
    def test_rule_test_path_islink_on_broken_link(self):
        """Test islink succeeds even when path is a broken link."""
        linkpath = '{0}_broken_link.txt'.format(self.testname)
        self._write_file(self.conffile, 'field: {0}'.format(linkpath))
        os.symlink('does_not_exist', linkpath)
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('islink'))
        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.field, linkpath)

    @unittest2.skipUnless(sys.platform.startswith('linux'), 'requires linux')
    def test_rule_test_path_islink_on_file(self):
        """Test islink fails when path is a file."""
        filepath = '{0}_existing_file.txt'.format(self.testname)
        self._write_file(self.conffile, 'field: {0}'.format(filepath))
        self._write_file(filepath, 'test file')
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('islink'))
        with self.assertRaisesRegex(
                ParseError, '"{0}" is not a symlink'.format(filepath)):
            _ = confp.parse_file(self.conffile)

    # Tests of '!islink'
    @unittest2.skipUnless(sys.platform.startswith('linux'), 'requires linux')
    def test_rule_test_path_not_islink_on_missing(self):
        """Test !islink succeeds when path is missing."""
        missingpath = 'does_not_exist'
        self._write_file(self.conffile, 'field: {0}'.format(missingpath))
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('!islink'))
        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.field, missingpath)

    @unittest2.skipUnless(sys.platform.startswith('linux'), 'requires linux')
    def test_rule_test_path_not_islink_on_broken_link(self):
        """Test islink fails when path is a link."""
        linkpath = '{0}_broken_link.txt'.format(self.testname)
        self._write_file(self.conffile, 'field: {0}'.format(linkpath))
        os.symlink('does_not_exist', linkpath)
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('!islink'))
        with self.assertRaisesRegex(
                ParseError, '"{0}" is a symlink'):
            _ = confp.parse_file(self.conffile)

    # Tests of 'ismount'
    @unittest2.skipUnless(sys.platform.startswith('linux'), 'requires linux')
    def test_rule_test_path_ismount_on_reguler_dir(self):
        """Test ismount fails on a regular directory."""
        dirname = '{0}_dir_not_mount'.format(self.testname)
        self._write_file(self.conffile, 'field: {0}'.format(dirname))
        os.mkdir(dirname)
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('ismount'))
        with self.assertRaisesRegex(
                ParseError, '"{0}" is not a mount point'.format(dirname)):
            confp.parse_file(self.conffile)

    # Tests of '!ismount'
    @unittest2.skipUnless(sys.platform.startswith('linux'), 'requires linux')
    def test_rule_test_path_not_ismount_on_regular_dir(self):
        """Test !ismount succeeds on a regular directory."""
        dirname = '{0}_dir_not_mount'.format(self.testname)
        self._write_file(self.conffile, 'field: {0}'.format(dirname))
        os.mkdir(dirname)
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('!ismount'))
        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.field, dirname)

    # Tests of 'exists' and 'isdir'
    def test_rule_test_path_exists_isdir_missing(self):
        """Test exists and isdir in that order tests exists first."""
        self._write_file(self.conffile, 'field: does_not_exist')
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('exists', 'isdir'))
        with self.assertRaisesRegex(
                ParseError, '"does_not_exist" does not exist'):
            confp.parse_file(self.conffile)

    def test_rule_test_path_exists_isdir_on_file(self):
        """Test exists and isdir in that order tests isdir second."""
        filepath = '{0}_existing_file.txt'.format(self.testname)
        self._write_file(filepath, 'test file')
        self._write_file(self.conffile, 'field: {0}'.format(filepath))
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('exists', 'isdir'))
        with self.assertRaisesRegex(
                ParseError, '"{0}" is not a directory'.format(filepath)):
            confp.parse_file(self.conffile)

    def test_rule_test_path_isdir_exists_missing(self):
        """Test isdir and exists in that order tests isdir first."""
        self._write_file(self.conffile, 'field: does_not_exist')
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('exists', 'isdir'))
        with self.assertRaisesRegex(
                ParseError, '"does_not_exist" is not a directory'):
            confp.parse_file(self.conffile)

    # Tests of 'isfile' and 'islink'
    @unittest2.skipUnless(sys.platform.startswith('linux'), 'requires linux')
    def test_rule_test_path_islink_isfile_on_link(self):
        """Test islink, isfile succeeds when path is a link."""
        filepath = '{0}_existing_file.txt'.format(self.testname)
        linkpath = '{0}_existing_link.txt'.format(self.testname)
        self._write_file(self.conffile, 'field: {0}'.format(linkpath))
        self._write_file(filepath, 'test file')
        os.symlink(filepath, linkpath)
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('islink', 'isfile'))
        conf = confp.parse_file(self.conffile)
        self.assertEqual(conf.field, linkpath)

    @unittest2.skipUnless(sys.platform.startswith('linux'), 'requires linux')
    def test_rule_test_path_islink_isfile_on_broken_link(self):
        """Test islink, isfile fails when path is a broken link."""
        linkpath = '{0}_existing_link.txt'.format(self.testname)
        self._write_file(self.conffile, 'field: {0}'.format(linkpath))
        os.symlink('does_not_exist', linkpath)
        confp = YamlConfigParser()
        confp.add_rule('field', test=test.is_file_path('islink', 'isfile'))
        with self.assertRaisesRegex(
                ParseError, '"{0}" is not a file'.format(linkpath)):
            confp.parse_file(self.conffile)


class RuleTestAndPathTypeChecksOnOptionalPaths(TestCase):
    """Test path types and rule tests on optional fields.

    Optional rules cause the path to be assigned a value of None when
    omitted, and in such cases, the path_type and test checks
    would fail if they were run but should not be.  If an optional
    rule is omitted, the type checking and test functions should be
    skipped.

    """

    def test_optional_int_type_present_int_good(self):
        """An optional path that is present should get type checked."""
        confp = YamlConfigParser()
        confp.add_rule('optintfield', path_type=int, optional=True)
        conf = self._test_conf_good(confp, 'optintfield: 42')
        self.assertEqual(conf.optintfield, 42)

    def test_optional_int_type_present_notint_bad(self):
        """An optional path that is present should get type checked."""
        confp = YamlConfigParser()
        confp.add_rule('optintfield', path_type=int, optional=True)
        self._test_conf_bad(
            confp=confp,
            conftext='optintfield: aaaaa',
            excrex='"optintfield" has type str not type int')

    def test_optional_int_type_missing_good(self):
        """An optional path that is missing should not get type checked."""
        confp = YamlConfigParser()
        confp.add_rule('optintfield', path_type=int, optional=True)
        conf = self._test_conf_good(confp, 'optintfield:')
        self.assertIsNone(conf.optintfield)

    def test_optional_regex_test_present_match_good(self):
        """Rule tests should be run on an optional path that is present."""
        confp = YamlConfigParser()
        confp.add_rule(
            'optrexfield', optional=True, test=test.is_regex('aaaaa'))
        conf = self._test_conf_good(confp, 'optrexfield: aaaaa')
        self.assertEqual(conf.optrexfield, 'aaaaa')

    def test_optional_regex_test_present_nomatch_bad(self):
        """Rule tests should be run on an optional path that is present."""
        confp = YamlConfigParser()
        confp.add_rule(
            'optrexfield', optional=True, test=test.is_regex('aaaaa'))
        self._test_conf_bad(
            confp=confp,
            conftext='optrexfield: AAAAA',
            excrex='"AAAAA" does not match /aaaaa/')

    def test_optional_regex_test_missing_good(self):
        """Rule tests should not be run on an optional path that is missing."""
        confp = YamlConfigParser()
        confp.add_rule(
            'optrexfield', optional=True, test=test.is_regex('aaaaa'))
        conf = self._test_conf_good(confp, 'optrexfield:')
        self.assertIsNone(conf.optrexfield)


class RuleTestAndPathTypeChecksOnDefaults(TestCase):
    """Test path types and rule tests on fields that take defaults.

    Defaults can be arbitrary types but they have to pass the same
    path_type and test checks that conffile supplied values do.
    This can cause confusion if encountered in operations, since the
    error message is a bit misleading.  The conffile writer gets a
    type error for a value that they did not provide.

    """

    def test_default_type_string_basic_good(self):
        """Defaulting to a str type is supported."""
        confp = YamlConfigParser()
        confp.add_rule('deffield', default='zzzzz')
        conf = self._test_conf_good(confp, 'deffield:')
        self.assertEqual(conf.deffield, 'zzzzz')

    def test_default_type_string_type_check_good(self):
        """Default value should pass path_type check."""
        confp = YamlConfigParser()
        confp.add_rule('deffield', path_type=str, default='zzzzz')
        conf = self._test_conf_good(confp, 'deffield:')
        self.assertEqual(conf.deffield, 'zzzzz')

    def test_default_type_string_type_check_bad(self):
        """Default value should fail path_type check."""
        confp = YamlConfigParser()
        confp.add_rule('deffield', path_type=str, default=42)
        self._test_conf_bad(
            confp=confp,
            conftext='deffield:',
            excrex='"deffield" has type int not type str')

    def test_default_type_string_test_check_good(self):
        """Default value should pass test check."""
        confp = YamlConfigParser()
        confp.add_rule(
            'deffield', default='zzzzz', test=test.is_regex('[a-z]{5}'))
        conf = self._test_conf_good(confp, 'deffield:')
        self.assertEqual(conf.deffield, 'zzzzz')

    def test_default_type_string_test_check_bad(self):
        """Default value should fail test check."""
        confp = YamlConfigParser()
        confp.add_rule(
            'deffield', default='zzzzz', test=test.is_regex('[A-Z]{5}'))
        self._test_conf_bad(
            confp=confp,
            conftext='deffield:',
            excrex=r'"zzzzz" does not match /\[A-Z\]\{5\}/')

    def test_default_type_int_basic_good(self):
        """Defaulting to a int type is supported."""
        confp = YamlConfigParser()
        confp.add_rule('deffield', default=42)
        conf = self._test_conf_good(confp, 'deffield:')
        self.assertEqual(conf.deffield, 42)

    def test_default_type_int_type_check_good(self):
        """Default value should pass path_type check."""
        confp = YamlConfigParser()
        confp.add_rule('deffield', path_type=int, default=42)
        conf = self._test_conf_good(confp, 'deffield:')
        self.assertEqual(conf.deffield, 42)

    def test_default_type_int_type_check_bad(self):
        """Default value should fail path_type check."""
        confp = YamlConfigParser()
        confp.add_rule('deffield', path_type=int, default='42')
        self._test_conf_bad(
            confp=confp,
            conftext='deffield:',
            excrex='"deffield" has type str not type int')

    def test_default_type_int_test_check_good(self):
        """Default value should pass test check."""
        confp = YamlConfigParser()
        confp.add_rule('deffield', default=42, test=test.is_interval(40, 50))
        conf = self._test_conf_good(confp, 'deffield:')
        self.assertEqual(conf.deffield, 42)

    def test_default_type_int_test_check_bad(self):
        """Default value should fail test check."""
        confp = YamlConfigParser()
        confp.add_rule('deffield', default=42, test=test.is_interval(50, 60))
        self._test_conf_bad(
            confp=confp,
            conftext='deffield:',
            excrex=r'42 is below the interval \[50, 60\)')

    def test_default_type_bool_type_check_good(self):
        """Default value should pass path_type check."""
        confp = YamlConfigParser()
        confp.add_rule('deffield', path_type=bool, default=False)
        conf = self._test_conf_good(confp, 'deffield:')
        self.assertEqual(conf.deffield, False)

    def test_default_type_bool_type_check_bad(self):
        """Default value should fail path_type check."""
        confp = YamlConfigParser()
        confp.add_rule('deffield', path_type=bool, default=0)
        self._test_conf_bad(
            confp=confp,
            conftext='deffield:',
            excrex='"deffield" has type int not type bool')

    def test_default_type_date_type_check_good(self):
        """Default value should pass path_type check."""
        confp = YamlConfigParser()
        confp.add_rule('deffield', path_type=date, default=date(1970, 1, 1))
        conf = self._test_conf_good(confp, 'deffield:')
        self.assertEqual(conf.deffield, date(1970, 1, 1))

    def test_default_type_date_type_check_bad(self):
        """Default value should fail path_type check."""
        confp = YamlConfigParser()
        confp.add_rule('deffield', path_type=date, default='1970-01-01')
        self._test_conf_bad(
            confp=confp,
            conftext='deffield:',
            excrex='"deffield" has type str not type date')
