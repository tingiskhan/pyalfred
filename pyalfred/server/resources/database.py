from typing import Union, List
from sqlalchemy.orm import scoped_session, sessionmaker
from falcon.status_codes import HTTP_500
from logging import Logger
from ..utils import make_base_logger
from pyalfred.contract.utils import chunk, Constants, serialize, deserialize
from pyalfred.contract.schema import AutoMarshmallowSchema
from pyalfred.contract import TreeParser


class DatabaseResource(object):
    def __init__(
        self,
        schema: AutoMarshmallowSchema,
        session_factory: Union[scoped_session, sessionmaker],
        logger: Logger = None,
        create_ignore: List[str] = None,
    ):
        """
        Implements a base resources for exposing database models.
        :param schema: The schema to use, must be marshmallow.Schema
        :param session_factory: The sqlalchemy scoped_session object to use
        :param logger: The logger to use
        :param create_ignore: Fields of the class to ignore deserializing when creating object. E.g. usually the PKs
        """

        self.schema = schema
        self.session_factory = session_factory
        self.logger = logger or make_base_logger(schema.endpoint())
        self._create_ignore = create_ignore

    @property
    def model(self):
        return self.schema.Meta.model

    def on_get(self, req, res):
        session = self.session_factory()

        try:
            query = session.query(self.model).with_for_update()
            filt = req.params.get("filter", None)
            if filt:
                tb = TreeParser(self.model)
                be = tb.from_string(filt)
                query = query.filter(be)

            latest = req.params.get("latest", "false").lower() == "true"
            if not latest:
                q_res = query.all()
            else:
                q_res = query.order_by(self.model.id.desc()).first()
                q_res = [q_res] if q_res is not None else []

            res.media = serialize(q_res, self.schema, many=True)
        except Exception as e:
            self.logger.exception(e)
            res.status = HTTP_500
            res.media = f"{e.__class__.__name__}: {e}"

        self.session_factory.remove()

        return res

    def on_put(self, req, res):
        objs = deserialize(req.media, self.schema, many=True, dump_only=self._create_ignore)
        self.logger.info(f"Now trying to create {len(objs):n} objects")
        session = self.session_factory()

        try:
            for c in chunk(objs, Constants.ChunkSize.value):
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
            for c in chunk(objs, Constants.ChunkSize.value):
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
