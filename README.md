# Schema checker #

Another schema validator :)

[![Build Status](https://travis-ci.org/moff4/schema_schecker.svg?branch=master)](https://travis-ci.org/moff4/schema_schecker)
[![CodeFactor](https://www.codefactor.io/repository/github/moff4/schema_schecker/badge)](https://www.codefactor.io/repository/github/moff4/schema_schecker)
[![codecov](https://codecov.io/gh/moff4/schema_schecker/branch/master/graph/badge.svg)](https://codecov.io/gh/moff4/schema_schecker)

Features:
* Can validate any dict object (not only json)
* Very customizeble

## Tutorial

Base validation function:
```python
def validate(obj: dict, schema: dict) -> dict:
    ... 
```
where
```
obj - some object
schema - schema_checker
schema ::= type of this object : list/dict/str/int/float (can be tuple of types) or "const"/"enum"
  OR
schema ::= dict - {
  type         : type of this object : "list/tuple/dict/str/int/float or "const"
  "value"      : need for obj type of
                   - list/tuple - is schema for all elements in list
                   - dict - dict[key -> schema]
                   - const - some value to be compared with using method
                   - enum - list/set/dict/tuple to check if obj __contains__ in "value"
  "any_key"     : need for obj type of dict - schema for all keys (ignores if value is set)
  "default"    : default value if this object does not exists (if callable will be called)
  "filter"     : any of
                   - Callable[value -> bool] - if false then raise error
                   - Iterable[Callable[value -> bool]] - if any of them return false then raise error
  "pre_call"   : any of
                   - Callable[value -> value] - will be called before checking type and call filter's functions
                   - Iterable[Callable[value -> value]] - will call all of them
  "post_call"  : any of
                   - Callable[value -> value] - will be called after checking type and call filter's functions
                   - Iterable[Callable[value -> value]] - will call all of them
  "blank"      : raise error if value is blank
  "max_length" : extra check of length (len)
  "min_length" : extra check of length (len)
  "unexpected" : allow unexpected keys (for dict)
  "errmsg"     : will be in ValueError in case of error on this level
}
```

#### Extras

##### decorator_constructor

`def decorator_constructor(getter, setter)`

`getter` must:
 - take same args as the function that'll be decorated
 - return dict for the schema validator
 
`setter` must:
 - take 3 args: validated dict, source positional args as tuple, sourse keyword args as dict
 - return tuple and dict for positional and keywords args for the function tha'll be decorated

returns parameterized decorator, that expects schema

##### kw_validator

`def kw_validator(schema)`

Validate only keyword args and ignores all positional 
This decorator is the result of decorator_constructor


##### pos_validator

`def pos_validator(schema)`

Validate only positional args and ignores all keywords 
This decorator is the result of decorator_constructor


##### args_validator
`def args_validator(pos_schema: Dict[str, Any], kw_schema: Dict[str, Any]):`

Validate both positional and keywords args


## Examples

```python
from datetime import datetime, timedelta
from schema_checker import validate, kw_validator

# validate that obj is str
validate(
    obj='12345',
    schema={'type': str},
)  # result: '12345'

validate(
    obj=12345,
    schema={'type': str},
)  # raise ValueError

# check if value is int and less then 5
validate(
    obj={'some_key': 10},
    schema={
        'type': dict,
        'value': {
            'some_key': {
                'type': int,
                'filter': lambda x: x < 5,
            },
        }
    },
)  # raise ValueError 


# convert obj to datetime and compare with today's date
validate(
    obj='10.12.19',
    schema={
        'type': datetime,
        'pre_call': lambda x: datetime.strptime(x, '%d.%m.%y'),
        'filter': lambda x: (datetime.today() - timedelta(year=1)) <= x <= datetime.today(),  
    },
)  # result: datetime.datetime(2019, 12, 10, 0, 0)


@kw_validator({'type': dict, 'values': {'a': str}})
def func(a):
    return a

func(123)  # ok
func('123')  # ok
func(a='123')  # ok
func(a=123)  # raise ValueError

```
 
