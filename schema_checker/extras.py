
from typing import Callable

from .jschema import validate


def decorator_constructor(getter: Callable, setter: Callable):
    def validator(schema):
        def decorator(func):
            def wrap(*a, **b):
                a, b = setter(validate(getter(*a, **b), schema), a, b)
                return func(*a, **b)
            return wrap
        return decorator
    return validator


# ignores positional args
kw_validator = decorator_constructor(
    getter=lambda *a, **b: b,
    setter=lambda data, *a, **b: (a, data),
)
