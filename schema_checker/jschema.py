
from typing import Any, Dict, NoReturn

ObjType = Any
SchemaType = Dict[str, Any]


def _apply(obj: ObjType, schema: SchemaType, key: str) -> ObjType:
    def get_type(sch) -> Any:
        return sch[type if type in sch else 'type']

    def default(value) -> Any:
        return value() if callable(value) else value

    def on_error(schema, msg) -> NoReturn:
        if isinstance(schema, dict):
            msg = schema.get('errmsg', msg)
        raise ValueError(msg)

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

    schema_type = get_type(schema)
    if schema_type in {'const', 'enum'}:
        if 'value' not in schema:
            on_error(schema, 'schema for "enum" must contain "value"')
        if schema_type == 'enum':
            if obj not in schema['value']:
                on_error(schema, '"{}" is not in enum "{}"')
        elif obj != schema['value']:
            on_error(schema, '"{}" is not allowed as "{}"'.format(obj, key))
    else:
        if not isinstance(obj, schema_type):
            on_error(schema,
                'expected type "{}" {} ; got {}'.format(
                    schema_type,
                    extra,
                    type(obj),
                ),
            )
        if 'filter' in schema and not schema['filter'](obj):
            on_error(schema, '"{}" not passed filter'.format(key))
        if schema.get('blank') is False and not obj:
            on_error(schema, '"{}" is blank'.format(key))
        if 'max_length' in schema and len(obj) > schema['max_length']:
            on_error(schema, '"{}" > max_length'.format(key))
        if 'min_length' in schema and len(obj) < schema['min_length']:
            on_error(schema, '"{}" < min_length'.format(key))

        if issubclass(schema_type, (list, tuple)):
            if 'value' in schema:
                try:
                    obj = schema_type(_apply(i, schema['value'], key=key) for i in obj)
                except ValueError as ex:
                    on_error(schema, ex)
        elif issubclass(schema_type, dict):
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
                        on_error(schema,
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
                        on_error(schema, 'expected keys "{}" {}'.format('", "'.join([str(i) for i in missed]), extra))

                try:
                    new_obj.update(
                        {
                            i:
                            default(schema['value'][i]['default'])
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
                    on_error(schema, ex)
                obj = new_obj
            elif 'any_key' in schema:
                try:
                    obj = {i: _apply(obj[i], schema['any_key'], i) for i in obj}
                except ValueError as ex:
                    on_error(schema, ex)

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