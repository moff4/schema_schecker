# Schema checker #

Another schema validator :)

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
schema - json_validator
key is name of top-level object (or None) ; (for log)
schema ::= type of this object : list/dict/str/int/float or "const"
  OR
schema ::= dict - {
  type         : type of this object : "list/dict/str/int/float or "const"
  "value"      : need for obj type of
                   - list - is schema for all elements in list
                   - dict - dict[key -> schema]
                   - const - list or set (or iterable) of allowed values
  "any_key"     : need for obj type of dict - schema for all keys (ignores if value is set)
  "default"    : default value if this object does not exists (if callable will be called)
  "filter"     : function value -> bool - if false then raise error
  "pre_call"   : function value -> value - will be called before cheking filter and value
  "post_call"  : function value -> value - will be called after cheking filter and value
  "blank"      : raise error if value is blank
  "max_length" : extra check of length (len)
  "min_length" : extra check of length (len)
  "unexpected" : allow unexpected keys (for dict)
}
```

## Examples

```python
from datetime import datetime, timedelta
from schema_checker import validate

validate(
    obj='12345',
    schema={'type': str},
)  # result: '12345'

validate(
    obj=12345,
    schema={'type': str},
)  # raise ValueError

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


validate(
    obj='10.12.19',
    schema={
        'type': datetime,
        'pre_call': lambda x: datetime.strptime(x, '%d.%m.%y'),
        'filter': lambda x: (datetime.today() - timedelta(year=1)) <= x <= datetime.today(),  
    },
)  # result: datetime.datetime(2019, 12, 10, 0, 0)

```
