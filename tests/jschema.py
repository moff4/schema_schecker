
import unittest

from schema_checker import validate


class TestJschema(unittest.TestCase):

    def do_test(self, obj, schema, result, expect=True, msg=None):
        try:
            if expect:
                self.assertEqual(validate(obj, schema), result)
            else:
                self.assertNotEqual(validate(obj, schema), result)
        except ValueError as e:
            self.assertFalse(expect)
            if msg:
                self.assertEqual(str(e), msg)

    def test_schema_fail(self):
        self.do_test(123, '123', 123, False)

    def test_simple_const(self):
        obj = '123'
        self.do_test(obj, 'const', obj)
        obj = 123
        self.do_test(obj, 'const', obj)

    def test_simple_str(self):
        obj = '123'
        self.do_test(obj, {'type': str}, obj)
        obj = 123
        self.do_test(obj, {'type': str}, obj, False)

    def test_simpler_str(self):
        obj = '123'
        self.do_test(obj, str, obj)
        obj = 123
        self.do_test(obj, str, obj, False)

    def test_simple_int(self):
        obj = 100500
        self.do_test(obj, {'type': int}, obj)
        obj = '100500'
        self.do_test(obj, {'type': int}, obj, False)

    def test_simpler_int(self):
        obj = 100500
        self.do_test(obj, int, obj)
        obj = '100500'
        self.do_test(obj, int, obj, False)

    def test_simple_float(self):
        obj = 1.001
        self.do_test(obj, {'type': float}, obj)
        obj = 1
        self.do_test(obj, {'type': float}, obj, False)

    def test_simpler_float(self):
        obj = 1.001
        self.do_test(obj, float, obj)
        obj = 1
        self.do_test(obj, float, obj, False)

    def test_simple_bool(self):
        obj = True
        self.do_test(obj, {'type': bool}, obj)
        obj = 1
        self.do_test(obj, {'type': bool}, obj, False)

    def test_simpler_bool(self):
        obj = True
        self.do_test(obj, bool, obj)
        obj = 1
        self.do_test(obj, bool, obj, False)

    def test_simple_dict(self):
        obj = {'1': 2, 'abc': 'cde'}
        self.do_test(
            obj,
            {
                'type': dict,
            },
            obj,
        )

    def test_dict(self):
        obj = {'1': 2, 'abc': 'cde'}
        self.do_test(
            obj,
            {
                'type': dict,
                'value': {
                    '1': int,
                    'abc': str,
                },
            },
            obj,
        )

    def test_dict_comples(self):
        obj = {
            '1': 123,
            '2': 42,
        }
        schema = {
            type: dict,
            'value': {
                '2': int,
                '3': {
                    type: int,
                    'default': 77,
                }
            },
            'unexpected': True,
        }
        self.do_test(
            obj=obj,
            schema=schema,
            result={
                '1': 123,
                '2': 42,
                '3': 77,
            }
        )

    def test_dict_fail(self):
        obj = {}
        self.do_test(
            obj,
            {
                'type': dict,
                'value': {
                    '1': {
                        'type': int,
                        'default': 2,
                    },
                    'abc': str,
                },
            },
            {'1': 2},
            False,
        )

    def test_simple_list(self):
        obj = ['1', 2, 'abc', 'cde']
        self.do_test(obj, {'type': list}, obj)

    def test_list(self):
        obj = ['1', '2', 'abc', 'cde']
        self.do_test(
            obj,
            {
                'type': list,
                'value': {
                    'type': str,
                }
            },
            obj,
        )

    def test_simple_tuple_ok(self):
        obj = ('1', 2, 'abc', 'cde')
        self.do_test(obj, {'type': tuple}, obj)

    def test_simple_tuple_fail(self):
        obj = ['1', 2, 'abc', 'cde']
        self.do_test(obj, {'type': tuple}, obj, False)

    def test_tuple_ok(self):
        obj = (1, 2, 123, 42)
        self.do_test(obj, {'type': tuple, 'value': int}, obj)

    def test_tuple_fail(self):
        obj = ('1', 2, 'abc', 'cde')
        self.do_test(obj, {'type': tuple, 'value': int}, obj, False)

    def test_simple_const_ok(self):
        obj = {'1': 123}
        schema = {
            'type': dict,
            'any_key': {
                'type': 'const',
                'value': 123,
            }
        }
        self.do_test(obj, schema, obj)

    def test_simple_const_fail(self):
        obj = {'1': 123}
        schema = {
            'type': dict,
            'any_key': {
                'type': 'const',
                'value': 122,
            }
        }
        self.do_test(obj, schema, obj, False)

    def test_const(self):
        obj = {
            '1': '2',
            '2': 10,
        }
        self.do_test(
            obj,
            {
                'type': dict,
                'value': {
                    '1': {
                        'type': 'const',
                        'value': '2',
                    },
                    '2': {
                        'type': 'const',
                        'value': 10,
                    },
                },
            },
            obj,
        )

    def test_default(self):
        obj = {'1': '2'}
        schema = {
            'type': dict,
            'value': {
                '1': {'type': str},
                'abc': {
                    'type': str,
                    'default': 'default_value',
                }
            }
        }
        res_obj = dict(obj, abc='default_value')
        self.do_test(obj, schema, res_obj)

    def test_filter(self):
        obj = {'1': 2}
        schema = {
            'type': dict,
            'value': {
                '1': {
                    'type': int,
                    'filter': lambda x: x < 5,
                },
            }
        }
        res_obj = obj
        self.do_test(obj, schema, res_obj)

    def test_filter_error(self):
        obj = {'1': 10}
        schema = {
            'type': dict,
            'value': {
                '1': {
                    'type': int,
                    'filter': lambda x: x < 5,
                },
            }
        }
        res_obj = obj
        self.do_test(obj, schema, res_obj, False)

    def test_pre_call(self):
        obj = {'1': '1, 2, 3, 4, 5, 6, 7, 8, 9, 10'}
        schema = {
            'type': dict,
            'value': {
                '1': {
                    'type': int,
                    'pre_call': lambda x: sum(int(i.strip()) for i in x.split(',')),
                },
            }
        }
        res_obj = {'1': sum(range(11))}
        self.do_test(obj, schema, res_obj)

    def test_post_call(self):
        obj = {'1': '2'}
        schema = {
            'type': dict,
            'value': {
                '1': {
                    # type will be checked after pre_call and before post_call
                    'pre_call': int,
                    'type': int,
                    'filter': lambda x: x < 5,
                    'post_call': str,
                },
            }
        }
        res_obj = {'1': '2'}
        self.do_test(obj, schema, res_obj)

    def test_blank(self):
        schema = {
            'type': str,
            'blank': True,
        }
        self.do_test('', schema, '', True)
        schema = {
            'type': str,
            'blank': False,
        }
        self.do_test('', schema, '', False)

    def test_max_length(self):
        schema = {
            'type': str,
            'max_length': 10,
        }
        self.do_test('A' * 10, schema, 'A' * 10, True)
        schema = {
            'type': str,
            'max_length': 10,
        }
        self.do_test('A' * 11, schema, 'A' * 11, False)

    def test_min_length(self):
        schema = {
            'type': str,
            'min_length': 10,
        }
        self.do_test('A' * 10, schema, 'A' * 10, True)
        schema = {
            'type': str,
            'min_length': 10,
        }
        self.do_test('A' * 9, schema, 'A' * 9, False)

    def test_unexpected_ok(self):
        schema = {
            'type': dict,
            'value': {
                '1': {
                    'type': int,
                },
            },
            'unexpected': True,
        }
        obj = {
            '1': 2,
            'abc': 'def',
        }
        self.do_test(obj, schema, obj, True)

    def test_unexpected_error(self):
        schema = {
            'type': dict,
            'value': {
                '1': {
                    'type': int,
                },
            },
            'unexpected': False,
        }
        obj = {
            '1': 2,
            'abc': 'def',
        }
        self.do_test(obj, schema, obj, False)

    def test_anykey_ok(self):
        schema = {
            'type': dict,
            'anykey': {
                'type': int,
            },
            'unexpected': True,
        }
        obj = {
            '1': 2,
            'abc': 3,
        }
        self.do_test(obj, schema, obj, True)

    def test_anykey_error(self):
        schema = {
            'type': dict,
            'any_key': {
                'type': int,
            },
            'unexpected': True,
        }
        obj = {
            '1': 2,
            'abc': '3',
        }
        self.do_test(obj, schema, obj, False)

    def test_type_union(self):
        schema = {
            'type': dict,
            'value': {
                'a': (int, float),
                'b': (str, bytes),
            }
        }
        obj = {'a': 1, 'b': '123'}
        self.do_test(obj, schema, obj)
        obj = {'a': 1.0, 'b': '123'}
        self.do_test(obj, schema, obj)
        obj = {'a': 1, 'b': b'123'}
        self.do_test(obj, schema, obj)
        obj = {'a': 1.0, 'b': b'123'}
        self.do_test(obj, schema, obj)

    def test_msg(self):
        schema = {
            'type': dict,
            'any_key': int,
            'errmsg': 'here must be int',
        }
        obj = {'123': 'not int'}
        self.do_test(obj, schema, obj, False, 'here must be int')

    def test_simple_enum(self):
        schema = {
            'type': 'enum',
            'value': {'1', '2'},
        }
        obj = '1'
        self.do_test(obj, schema, obj)
        obj = '2'
        self.do_test(obj, schema, obj)
        obj = '3'
        self.do_test(obj, schema, obj, False)

    def test_simple_enum_schema_fail(self):
        schema = {
            'type': 'enum',
        }
        obj = '1'
        self.do_test(obj, schema, obj, False)

    def test_enum(self):
        obj = {
            '1': '2',
            '2': 10,
        }
        self.do_test(
            obj,
            {
                'type': dict,
                'value': {
                    '1': {
                        'type': 'enum',
                        'value': {'1', '2'},
                    },
                    '2': {
                        'type': 'enum',
                        'value': range(100),
                    },
                }
            },
            obj,
        )