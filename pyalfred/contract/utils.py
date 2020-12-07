from enum import Enum
from typing import List, Dict, Any, TypeVar
from .schema import AutoMarshmallowSchema


T = TypeVar("T")


def chunk(iterable, cs):
    for i in range(0, len(iterable), cs):
        yield iterable[i : i + cs]


class Constants(Enum):
    ChunkSize = 999
    InterfaceChunk = 9999


def serialize(objects: List[T], schema: AutoMarshmallowSchema, **kwargs) -> List[Dict[str, Any]]:
    return schema(many=kwargs.pop("many", True), **kwargs).dump(objects)


def deserialize(json: List[Dict[str, Any]], schema: AutoMarshmallowSchema, **kwargs) -> List[T]:
    res = schema(many=kwargs.pop("many", True), **kwargs).load(json)
    return [schema.Meta.model(**it) for it in res]
