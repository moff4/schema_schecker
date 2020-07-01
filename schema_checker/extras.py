
from typing import Callable, Dict, Any
import functools

from .jschema import validate


def decorator_constructor(getter: Callable, setter: Callable):
    def validator(schema: Dict[str, Any]):
        def decorator(func):
            @functools.wraps(func)
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

# ignores kw args
pos_validator = decorator_constructor(
    getter=lambda *a, **b: a,
    setter=lambda data, *a, **b: (data, b),
)


# validate both pos and kw args
def args_validator(pos_schema: Dict[str, Any], kw_schema: Dict[str, Any]):
    def decorator(func):
        @functools.wraps(func)
        def wrap(*a, **b):
            a = validate(a, pos_schema)
            b = validate(b, kw_schema)
            return func(*a, **b)
        return wrap
    return decorator
