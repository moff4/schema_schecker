
from typing import Any, Dict, NoReturn, TypeVar, Union, Type, Tuple, Callable, Iterable

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


def _check_dict_key(obj: ObjType, schema: Dict[str, Any], extra: str) -> ObjType:
    unex = {i for i in obj if i not in schema['value']}
    if unex and not schema.get('unexpected', False):
        _on_error(schema, 'Got unexpected keys: "{}" {};'.format('", "'.join([str(i) for i in unex]), extra))
    missed = {
        i
        for i in schema['value']
        if i not in obj and (not isinstance(schema['value'][i], dict) or 'default' not in schema['value'][i])
    }
    if missed:
        _on_error(schema, 'expected keys "{}" {}'.format('", "'.join([str(i) for i in missed]), extra))
    return {
        i: obj[i]
        for i in unex
    }


def _validate_dicts_value(obj: ObjType, schema: Dict[str, Any], extra: str) -> ObjType:
    new_obj = _check_dict_key(obj=obj, schema=schema, extra=extra)
    try:
        new_obj.update(
            {
                i: (
                    _default(schema['value'][i]['default'])
                    if i not in obj else
                    _apply(obj=obj[i], schema=schema['value'][i], key=i)
                )
                for i in schema['value']
            }
        )
    except ValueError as ex:
        _on_error(schema, ex)
    return new_obj


def _validate_dict(obj: ObjType, schema: Dict[str, Any], extra: str) -> ObjType:
    if 'value' in schema:
        obj = _validate_dicts_value(obj=obj, schema=schema, extra=extra)
    elif 'any_key' in schema:
        try:
            obj = {i: _apply(obj[i], schema['any_key'], i) for i in obj}
        except ValueError as ex:
            _on_error(schema, ex)
    return obj


def _check_filter(obj: ObjType, func: Union[Callable, Iterable[Callable]]) -> bool:
    return all(func(obj) for func in ([func] if callable(func) else func))


def _generic_checks(obj: ObjType, schema: SchemaType, schema_type: Type, extra: str, key: str) -> ObjType:
    if not isinstance(obj, schema_type):
        _on_error(schema, 'expected type "{}" {} ; got {}'.format(schema_type, extra, type(obj)))
    if 'filter' in schema and not _check_filter(obj, schema['filter']):
        _on_error(schema, '"{}" not passed filter'.format(key))
    if schema.get('blank') is False and not obj:
        _on_error(schema, '"{}" is blank'.format(key))
    if 'max_length' in schema and len(obj) > schema['max_length']:
        _on_error(schema, '"{}" > max_length'.format(key))
    if 'min_length' in schema and len(obj) < schema['min_length']:
        _on_error(schema, '"{}" < min_length'.format(key))
    return obj


def _validate_generic(obj: ObjType, schema: SchemaType, schema_type: Type, key: str, extra: str) -> ObjType:
    obj = _generic_checks(obj=obj, schema=schema, schema_type=schema_type, key=key, extra=extra)
    if issubclass(schema_type, (list, tuple)) and 'value' in schema:
        try:
            obj = schema_type(_apply(i, schema['value'], key=key) for i in obj)
        except ValueError as ex:
            _on_error(schema, ex)
    elif issubclass(schema_type, dict):
        obj = _validate_dict(obj=obj, schema=schema, extra=extra)
    return obj


def _validate(obj: ObjType, schema: SchemaType, key: str, extra: str) -> ObjType:
    schema_type = _get_type(schema)
    if schema_type in {'const', 'enum'}:
        return _validate_const_enum(obj=obj, schema=schema, schema_type=schema_type, key=key)
    return _validate_generic(obj=obj, schema=schema, schema_type=schema_type, extra=extra, key=key)


def _apply_callable(obj: ObjType, func: Union[Callable, Iterable[Callable]]) -> ObjType:
    for func in ([func] if callable(func) else func):
        obj = func(obj)
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
        obj = _apply_callable(obj, schema['pre_call'])

    obj = _validate(obj=obj, schema=schema, key=key, extra=extra)

    if 'post_call' in schema:
        obj = _apply_callable(obj, schema['post_call'])
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
    """
    return _apply(obj, schema, 'Top-level')
