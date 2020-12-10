from typing import Union, List, Type
from sqlalchemy.orm import scoped_session, sessionmaker
from falcon.status_codes import HTTP_500
from logging import Logger
from pyalfred.contract.utils import chunk, serialize, deserialize
from pyalfred.contract.schema import AutoMarshmallowSchema
from pyalfred.contract.query import QueryBuilder
from pyalfred.contract.utils import get_columns_in_base_mixin
from ..utils import make_base_logger
from ...constants import CHUNK_SIZE


class DatabaseResource(object):
    def __init__(
        self,
        schema: AutoMarshmallowSchema,
        session_factory: Union[scoped_session, sessionmaker],
        logger: Logger = None,
        mixin_ignore: Type[object] = None
    ):
        """
        Implements a base resources for exposing database models.
        :param schema: The schema to use, must be marshmallow.Schema
        :param session_factory: The sqlalchemy scoped_session object to use
        :param logger: The logger to use
        :param mixin_ignore: If all of your models inherit from a single mixin that defines server side generated
        columns, you may pass that here.
        """

        self.schema = schema
        self.session_factory = session_factory
        self.logger = logger or make_base_logger(schema.endpoint())

        self._create_ignore = []
        if mixin_ignore is not None:
            self._create_ignore += get_columns_in_base_mixin(mixin_ignore)

    @property
    def model(self):
        return self.schema.Meta.model

    @property
    def dump_only_fields(self):
        schema_fields_to_load = list(getattr(self.schema, "load_only_fields", []))

        return self._create_ignore + schema_fields_to_load

    def on_get(self, req, res):
        session = self.session_factory()

        try:
            query = session.query(self.model).with_for_update()
            filt = req.params.get("filter", None)
            if filt:
                query_builder = QueryBuilder(self.model)
                filter_ = query_builder.from_string(filt)
                query = query.filter(filter_)

            latest = req.params.get("latest", "false").lower() == "true"
            if not latest:
                query_result = query.all()
            else:
                query_result = query.order_by(self.model.id.desc()).first()
                query_result = [query_result] if query_result is not None else []

            res.media = serialize(query_result, self.schema, many=True)
        except Exception as e:
            self.logger.exception(e)
            res.status = HTTP_500
            res.media = f"{e.__class__.__name__}: {e}"

        self.session_factory.remove()

        return res

    def on_put(self, req, res):
        objs = deserialize(req.media, self.schema, dump_only=self.dump_only_fields, many=True)
        self.logger.info(f"Now trying to create {len(objs):n} objects")
        session = self.session_factory()

        try:
            for c in chunk(objs, CHUNK_SIZE):
                session.add_all(c)
                session.flush()

            session.commit()
            self.logger.info(f"Successfully created {len(objs):n} objects, now trying to serialize")
            res.media = serialize(objs, self.schema, many=True)
        except Exception as e:
            self.logger.exception(e)
            res.status = HTTP_500
            res.media = f"{e.__class__.__name__}: {e}"
            session.rollback()

        self.session_factory.remove()

        return res

    def on_delete(self, req, res):
        session = self.session_factory()

        try:
            nums = session.query(self.model).filter(self.model.id == req.params["id"]).delete("fetch")
            self.logger.info(f"Now trying to delete {nums:n} objects")
            session.commit()

            self.logger.info(f"Successfully deleted {nums:n} objects")
            res.media = {"deleted": nums}
        except Exception as e:
            self.logger.exception(e)
            session.rollback()
            res.media = f"{e.__class__.__name__}: {e}"
            res.status = HTTP_500

        self.session_factory.remove()

        return res

    def on_patch(self, req, res):
        objs = deserialize(req.media, self.schema, many=True)
        session = self.session_factory()
        self.logger.info(f"Now trying to update {len(objs):n} objects")

        try:
            for c in chunk(objs, CHUNK_SIZE):
                for obj in c:
                    session.merge(obj)

                session.flush()

            session.commit()
            self.logger.info(f"Successfully updated {len(objs):n} objects, now trying to serialize")
            res.media = serialize(objs, self.schema, many=True)
        except Exception as e:
            self.logger.exception(e)
            session.rollback()
            res.media = f"{e.__class__.__name__}: {e}"
            res.status = HTTP_500

        self.session_factory.remove()

        return res
