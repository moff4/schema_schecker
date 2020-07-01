
from unittest import TestCase

from schema_checker.extras import pos_validator, kw_validator, args_validator


class TestExtras(TestCase):

    def test_pos_validator_ok(self):
        func = pos_validator(
            {
                'type': tuple,
                'value': int,
            }
        )(lambda *a, **b: (a, b))
        a, b = func(1, 2, 3, a='123')
        self.assertEqual(a, (1, 2, 3))
        self.assertEqual(b, {'a': '123'})

    def test_pos_validator_fail(self):
        func = pos_validator(
            {
                'type': tuple,
                'value': int,
            }
        )(lambda *a, **b: print(a, b) or (a, b))

        try:
            self.assertEqual(func(1, 2, '3', a='123'), ...)
        except ValueError:
            ...  # ok

    def test_kw_validator_ok(self):
        func = kw_validator(
            {
                'type': dict,
                'any_key': int,
            }
        )(lambda *a, **b: (a, b))
        a, b = func(1, '2', 3, a=123, b=42)
        self.assertEqual(a, (1, '2', 3))
        self.assertEqual(b, {'a': 123, 'b': 42})

    def test_kw_validator_fail(self):
        func = kw_validator(
            {
                'type': dict,
                'any_key': int,
            }
        )(lambda *a, **b: print(a, b) or (a, b))

        try:
            self.assertEqual(func(1, '2', 3, a='123', b=42), ...)
        except ValueError:
            ...  # ok

    def test_args_validator_ok(self):
        func = args_validator(
            pos_schema={
                'type': tuple,
                'value': int,
            },
            kw_schema={
                'type': dict,
                'any_key': int,
            },
        )(lambda *a, **b: (a, b))
        a, b = func(1, 2, 3, a=123, b=42)
        self.assertEqual(a, (1, 2, 3))
        self.assertEqual(b, {'a': 123, 'b': 42})

    def test_args_validator_fail_pos(self):
        func = args_validator(
            pos_schema={
                'type': tuple,
                'value': int,
            },
            kw_schema={
                'type': dict,
                'any_key': int,
            }
        )(lambda *a, **b: print(a, b) or (a, b))

        try:
            self.assertEqual(func(1, '2', 3, a=123, b=42), ...)
        except ValueError:
            ...  # ok

    def test_args_validator_fail_kw(self):
        func = args_validator(
            pos_schema={
                'type': tuple,
                'value': int,
            },
            kw_schema={
                'type': dict,
                'any_key': int,
            }
        )(lambda *a, **b: print(a, b) or (a, b))

        try:
            self.assertEqual(func(1, 2, 3, a='123', b=42), ...)
        except ValueError:
            ...  # ok


    def test_args_validator_fail_both(self):
        func = args_validator(
            pos_schema={
                'type': tuple,
                'value': int,
            },
            kw_schema={
                'type': dict,
                'any_key': int,
            }
        )(lambda *a, **b: print(a, b) or (a, b))

        try:
            self.assertEqual(func(1, '2', 3, a='123', b=42), ...)
        except ValueError:
            ...  # ok
