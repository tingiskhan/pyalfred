from typing import Union, List, Type
from sqlalchemy.orm import scoped_session, sessionmaker
from logging import Logger
from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_200_OK
from pyalfred.contract.utils import chunk, serialize
from auto_schema import AutoMarshmallowSchema
from pyalfred.contract.query import QueryBuilder
from pyalfred.contract.utils import get_columns_in_base_mixin
from ..utils import make_base_logger, apply_filter_from_string
from ...constants import CHUNK_SIZE


def get_bool_from_string(x: str):
    return x.lower() == "true"


class DatabaseResource(HTTPEndpoint):
    schema = None
    session_factory = None
    logger = None

    _create_ignore = None

    @classmethod
    def make_endpoint(
        cls,
        schema: Type[AutoMarshmallowSchema],
        session_factory: Union[scoped_session, sessionmaker],
        logger: Logger = None,
        mixin_ignore: Type[object] = None,
        create_ignore: List[str] = None,
    ):
        """
        Implements a base resources for exposing database models.
        :param schema: The schema to use, must be marshmallow.Schema
        :param session_factory: The sqlalchemy scoped_session object to use
        :param logger: The logger to use
        :param mixin_ignore: If all of your models inherit from a single mixin that defines server side generated
        columns, you may pass that here.
        """

        _create_ignore = []
        if mixin_ignore is not None:
            _create_ignore += get_columns_in_base_mixin(mixin_ignore)
        elif create_ignore is not None:
            _create_ignore += create_ignore

        state_dict = {
            "schema": schema,
            "session_factory": session_factory,
            "logger": logger or make_base_logger(schema.__name__),
            "_create_ignore": _create_ignore,
        }

        return type(f"DatabaseResource_{schema.__name__}", (DatabaseResource,), state_dict)

    @property
    def model(self):
        return self.schema.Meta.model

    @property
    def fields_to_skip_on_create(self):
        schema_fields_to_load = list(getattr(self.schema, "load_only_fields", []))

        return self._create_ignore + schema_fields_to_load

    async def get(self, req: Request):
        session = self.session_factory()

        try:
            query = session.query(self.model).with_for_update()
            filter_ = req.query_params.get("filter", None)
            if filter_:
                query_builder = QueryBuilder(self.model)
                filter_ = query_builder.from_string(filter_)
                query = query.filter(filter_)

            ops = req.query_params.get("ops", "")
            result = apply_filter_from_string(self.model, query, ops.split(","))

            if result is None:
                result = list()
            elif not isinstance(result, list):
                result = [result]

            media = serialize(result, self.schema, many=True)
            status = HTTP_200_OK
        except Exception as e:
            self.logger.exception(e)
            status = HTTP_500_INTERNAL_SERVER_ERROR
            media = f"{e.__class__.__name__}: {e}"

        self.session_factory.remove()

        return JSONResponse(media, status)

    async def put(self, req: Request):
        batched = get_bool_from_string(req.query_params.get("batched", "false"))

        schema = self.schema(dump_only=self.fields_to_skip_on_create, many=True)
        objs = schema.load_instance(await req.json())

        self.logger.info(f"Now trying to create {len(objs):n} objects")
        session = self.session_factory()

        try:
            for c in chunk(objs, CHUNK_SIZE):
                session.add_all(c)
                session.flush()

            session.commit()
            self.logger.info(f"Successfully created {len(objs):n} objects, now trying to serialize")

            media = serialize(objs, self.schema, many=True) if not batched else []
            status = HTTP_200_OK
        except Exception as e:
            self.logger.exception(e)
            status = HTTP_500_INTERNAL_SERVER_ERROR
            media = f"{e.__class__.__name__}: {e}"
            session.rollback()

        self.session_factory.remove()

        return JSONResponse(media, status)

    async def delete(self, req: Request):
        session = self.session_factory()

        try:
            nums = session.query(self.model).filter(self.model.id == req.query_params["id"]).delete("fetch")
            self.logger.info(f"Now trying to delete {nums:n} objects")
            session.commit()

            self.logger.info(f"Successfully deleted {nums:n} objects")

            media = {"deleted": nums}
            status = HTTP_200_OK
        except Exception as e:
            self.logger.exception(e)
            session.rollback()
            media = f"{e.__class__.__name__}: {e}"
            status = HTTP_500_INTERNAL_SERVER_ERROR

        self.session_factory.remove()

        return JSONResponse(media, status)

    async def patch(self, req: Request):
        batched = get_bool_from_string(req.query_params.get("batched", "false"))

        schema = self.schema(many=True)
        objs = schema.load_instance(await req.json())

        session = self.session_factory()
        self.logger.info(f"Now trying to update {len(objs):n} objects")

        try:
            for c in chunk(objs, CHUNK_SIZE):
                for obj in c:
                    session.merge(obj)

                session.flush()

            session.commit()
            self.logger.info(f"Successfully updated {len(objs):n} objects, now trying to serialize")

            media = serialize(objs, self.schema, many=True) if not batched else []
            status = HTTP_200_OK
        except Exception as e:
            self.logger.exception(e)
            session.rollback()
            media = f"{e.__class__.__name__}: {e}"
            status = HTTP_500_INTERNAL_SERVER_ERROR

        self.session_factory.remove()

        return JSONResponse(media, status)
