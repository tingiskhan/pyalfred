from typing import Callable, Type, TypeVar, List, Union
from query_serializer import QueryBuilder
from ..utils import chunk, serialize, get_columns_in_base_mixin
from auto_schema import AutoMarshmallowSchema
from ...constants import INTERFACE_CHUNK_SIZE
from .base import BaseClient


T = TypeVar("T")


def decorator(f):
    def wrapper(self, objs: T or List[T], **kwargs):
        if not isinstance(objs, (list, tuple)):
            objs = [objs]

        if any(not isinstance(o, objs[0].__class__) for o in objs):
            raise ValueError()

        return f(self, objs, **kwargs)

    return wrapper


class Client(BaseClient):
    def __init__(self, base_url, mixin_ignore: Type[object] = None):
        """
        An interface for defining and creating.
        :param mixin_ignore: If you have a mixin whose columns you wish to ignore when creating.
        """
        super().__init__(base_url)

        self._load_only = list()
        if mixin_ignore is not None:
            self._load_only = get_columns_in_base_mixin(mixin_ignore)

    @classmethod
    def make_endpoint(cls, schema: Type[AutoMarshmallowSchema]) -> str:
        return schema.__name__.lower().replace("schema", "")

    def _load_only_fields(self, load_only, schema):
        res = load_only if any(load_only) else self._load_only
        return res + getattr(schema, "load_only_fields", [])

    @decorator
    def create(self, objects: Union[T, List[T]], load_only=None, batched=False) -> Union[T, List[T]]:
        """
        Create an object of type specified by Meta object in `schema`.
        :return: An object of type specified by Meta object in `schema`
        """

        res = list()
        schema = AutoMarshmallowSchema.get_schema(type(objects[0]))

        load_only_ = self._load_only_fields(load_only or list(), schema)
        endpoint = self.make_endpoint(schema)

        init_schema = schema(many=True)

        for c in chunk(objects, INTERFACE_CHUNK_SIZE):
            dump = serialize(c, schema, load_only=load_only_, many=True)
            req = self._make_request("put", endpoint, json=dump, params={"batched": batched})
            res.extend(init_schema.load_instance(self._send_request(req)))

        if any(res) and len(res) < 2:
            return res[0]

        return res

    def get(
        self, objtype: Type[T], f: Callable[[T], bool] = None, one=False, operations: str = None
    ) -> Union[T, List[T], None]:
        """
        Get an object of type specified by Meta object in `schema`.
        :param objtype: The object type to get
        :param f: Function for designing a filter
        :param one: Whether to get only one
        :param operations: Whether to apply any special operations
        :return: The object of type specified by Meta object in `schema`, or all
        """

        json = None
        schema = AutoMarshmallowSchema.get_schema(objtype)
        if f:
            fb = QueryBuilder(schema.Meta.model)
            json = fb.to_string(f(schema.Meta.model))

        req = self._make_request("get", endpoint=self.make_endpoint(schema), params={"filter": json, "ops": operations})

        init_schema = schema(many=True)
        res = init_schema.load_instance(self._send_request(req))

        if not one:
            return res

        if len(res) > 1:
            raise ValueError("More than 1 elements exist!")

        return next(iter(res), None)

    @decorator
    def delete(self, objects: Union[T, List[T]]) -> int:
        """
        Deletes an object with `id_` of type specified by Meta object in `schema`.
        :return: The number of affected items
        """

        deleted = 0
        schema = AutoMarshmallowSchema.get_schema(type(objects[0]))
        endpoint = self.make_endpoint(schema)
        for obj in objects:
            req = self._make_request("delete", endpoint=endpoint, params={"id": obj.id})
            resp = self._send_request(req)
            deleted += resp["deleted"]

        return deleted

    @decorator
    def update(self, objects: Union[T, List[T]], batched=False) -> List[T]:
        """
        Updates an object with the new values.
        :return: The update object
        """

        res = list()
        schema = AutoMarshmallowSchema.get_schema(type(objects[0]))
        endpoint = self.make_endpoint(schema)

        init_schema = schema(many=True)
        for c in chunk(objects, INTERFACE_CHUNK_SIZE):
            dump = serialize(c, schema, many=True)
            req = self._make_request("patch", endpoint, json=dump, params={"batched": batched})
            res.extend(init_schema.load_instance(self._send_request(req)))

        return res
