
from typing import Any, Dict, NoReturn, TypeVar, Union, Type, Tuple

ObjType = TypeVar('ObjType')
SchemaType = Union[str, Type, Tuple[Type], Dict[Union[str, Type], Any]]


def _get_type(sch: Dict[Union[str, Type], Any]) -> Any:
    return sch[type if type in sch else 'type']


def _default(value: Any) -> Any:
    return value() if callable(value) else value


def _on_error(schema: SchemaType, msg: Union[str, Exception]) -> NoReturn:
    if isinstance(schema, dict):
        msg = schema.get('errmsg', msg)
    raise ValueError(msg)


def _validate_const_enum(obj: ObjType, schema: Dict[str, Any], schema_type: str, key: str) -> ObjType:
    if 'value' not in schema:
        _on_error(schema, 'schema for "enum" must contain "value"')
    if schema_type == 'enum':
        if obj not in schema['value']:
            _on_error(schema, '"{}" is not in enum "{}"')
    elif obj != schema['value']:
        _on_error(schema, '"{}" is not allowed as "{}"'.format(obj, key))
    return obj


def _validate_dict(obj: ObjType, schema: Dict[str, Any], extra: str) -> ObjType:
    if 'value' in schema:
        new_obj = {}
        unex = {i for i in obj if i not in schema['value']}
        if unex:
            if schema.get('unexpected', False):
                new_obj.update(
                    {
                        i: obj[i]
                        for i in unex
                    }
                )
            else:
                _on_error(schema,
                          'Got unexpected keys: "{}" {};'.format(
                              '", "'.join([str(i) for i in unex]),
                              extra,
                          ),
                          )
        missed = {
            i
            for i in schema['value']
            if i not in obj and (not isinstance(schema['value'][i], dict) or 'default' not in schema['value'][i])
        }
        if missed:
            _on_error(schema, 'expected keys "{}" {}'.format('", "'.join([str(i) for i in missed]), extra))

        try:
            new_obj.update(
                {
                    i:
                        _default(schema['value'][i]['default'])
                        if i not in obj else
                        _apply(
                            obj=obj[i],
                            schema=schema['value'][i],
                            key=i,
                        )
                    for i in schema['value']
                }
            )
        except ValueError as ex:
            _on_error(schema, ex)
        obj = new_obj
    elif 'any_key' in schema:
        try:
            obj = {i: _apply(obj[i], schema['any_key'], i) for i in obj}
        except ValueError as ex:
            _on_error(schema, ex)
    return obj


def _validate(obj: ObjType, schema: SchemaType, key: str, extra: str) -> ObjType:
    schema_type = _get_type(schema)
    if schema_type in {'const', 'enum'}:
        obj = _validate_const_enum(obj=obj, schema=schema, schema_type=schema_type, key=key)
    else:
        if not isinstance(obj, schema_type):
            _on_error(schema, 'expected type "{}" {} ; got {}'.format(schema_type, extra, type(obj)))
        if 'filter' in schema and not schema['filter'](obj):
            _on_error(schema, '"{}" not passed filter'.format(key))
        if schema.get('blank') is False and not obj:
            _on_error(schema, '"{}" is blank'.format(key))
        if 'max_length' in schema and len(obj) > schema['max_length']:
            _on_error(schema, '"{}" > max_length'.format(key))
        if 'min_length' in schema and len(obj) < schema['min_length']:
            _on_error(schema, '"{}" < min_length'.format(key))

        if issubclass(schema_type, (list, tuple)) and 'value' in schema:
            obj = schema_type(_apply(i, schema['value'], key=key) for i in obj)
        elif issubclass(schema_type, dict):
            obj = _validate_dict(obj=obj, schema=schema, extra=extra)
    return obj


def _apply(obj: ObjType, schema: SchemaType, key: str) -> ObjType:
    extra = ''.join(['for ', key]) if key else ''
    if not isinstance(schema, (dict, type, tuple)) and schema not in {'const', 'enum'}:
        raise ValueError('schema must be type, dict, tuple or "const"/"enum" {}'.format(extra))

    if schema == 'const':
        return obj

    if isinstance(schema, (type, tuple)):
        if isinstance(obj, schema):
            return obj
        raise ValueError('"{}" is not type of "{}" {}'.format(obj, schema, extra))

    if 'pre_call' in schema:
        obj = schema['pre_call'](obj)

    obj = _validate(obj=obj, schema=schema, key=key, extra=extra)

    if 'post_call' in schema:
        obj = schema['post_call'](obj)
    return obj


def validate(obj: ObjType, schema: SchemaType) -> ObjType:
    """
        obj - some object
        schema - schema_checker
        schema ::= type of this object : list/dict/str/int/float (can be tuple of types) or "const"/"enum"
          OR
        schema ::= dict - {
          type         : type of this object : "list/tuple/dict/str/int/float or "const"
          "value"      : need for obj type of
                           - list/tuple - is schema for all elements in list
                           - dict - dict[key -> schema]
                           - const - list or set (or iterable) of allowed values
                           - enum - list/set/dict/tuple to check if obj __contains__ in "value"
          "any_key"     : need for obj type of dict - schema for all keys (ignores if value is set)
          "default"    : default value if this object does not exists (if callable will be called)
          "filter"     : function value -> bool - if false then raise error
          "pre_call"   : function value -> value - will be called before cheking filter and value
          "post_call"  : function value -> value - will be called after cheking filter and value
          "blank"      : raise error if value is blank
          "max_length" : extra check of length (len)
          "min_length" : extra check of length (len)
          "unexpected" : allow unexpected keys (for dict)
          "errmsg"     : will be in ValueError in case of error on this level
        }
    """
    return _apply(obj, schema, 'Top-level')