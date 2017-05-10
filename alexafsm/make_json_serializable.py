"""
Module that monkey-patches json module when it's imported so JSONEncoder.default() automatically
checks for a special "to_json()" method and uses it to encode the object if found.

See http://stackoverflow.com/a/18561055/257583
"""

from json import JSONEncoder


def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)


def nested_get_obj_or_json(obj):
    if hasattr(obj, 'to_json'):
        return nested_get_obj_or_json(obj.to_json())
    elif isinstance(obj, (list, tuple)):
        return [nested_get_obj_or_json(e) for e in obj]
    elif isinstance(obj, dict):
        return {k: nested_get_obj_or_json(v) for k, v in obj.items()}
    else:
        return obj


def _iterencode(self, obj, _one_shot=False):
    gen = _iterencode.iterencode(nested_get_obj_or_json(obj), _one_shot)
    for chunk in gen:
        yield chunk


_default.default = JSONEncoder().default  # Save unmodified default.
_iterencode.iterencode = JSONEncoder().iterencode
JSONEncoder.default = _default  # replacement
JSONEncoder.iterencode = _iterencode  # replacement
