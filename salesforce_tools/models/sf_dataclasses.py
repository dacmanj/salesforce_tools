from dataclasses import dataclass, fields
from dataclasses_json import dataclass_json
from functools import wraps
from enum import Enum
from datetime import datetime


def _wrap_init(original_init):
    @wraps(original_init)
    def __init__(self, *args, **kwargs):
        for f in fields(self):
            alias = f.metadata.get("alias")
            if alias is not None:
                try:
                    value = kwargs.pop(alias)
                    kwargs[f.name] = value
                except KeyError:
                    value = None
            else:
                value = kwargs.get(f.name)
            if issubclass(f.type, Enum) and value:
                kwargs[f.name] = f.type(value)

            if f.type == datetime and value:
                try:
                    kwargs[f.name] = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.000+0000")
                except ValueError:
                    kwargs[f.name] = value

        original_init(self, *args, **kwargs)

    return __init__


def to_api(self):
    d = self.__dict__.copy()
    for f in fields(self):
        alias = f.metadata.get("alias")
        if alias is not None:
            value = d.pop(f.name, None)
            if value:
                d[alias] = value
        else:
            value = d.get(f.name)

        if f.type == datetime and value:
            try:
                d[f.name] = datetime.strftime(value, "%Y-%m-%dT%H:%M:%S.000+0000")
            except ValueError:
                d[f.name] = value

    return d


def apply_init(cls):
    original_init = cls.__init__
    cls.__init__ = _wrap_init(original_init)
    cls.to_api = to_api
    return cls


def salesforce_api_dataclass(func):
    #dataclass_json()
    return apply_init(dataclass(func))
