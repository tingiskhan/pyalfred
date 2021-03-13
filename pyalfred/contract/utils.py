from typing import List, Dict, Any, TypeVar, Type
from sqlalchemy import Column
from auto_schema import AutoMarshmallowSchema

T = TypeVar("T")


def chunk(iterable, cs):
    for i in range(0, len(iterable), cs):
        yield iterable[i : i + cs]


def serialize(objects: List[T], schema: AutoMarshmallowSchema, **kwargs) -> List[Dict[str, Any]]:
    return schema(many=kwargs.pop("many", True), **kwargs).dump(objects)


def get_columns_in_base_mixin(obj: Type[object]):
    return [k for (k, v) in vars(obj).items() if isinstance(v, Column)]
