from falcon import API as Api
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
import os
from time import sleep
from numpy.random import uniform
from pyalfred.server.resources import DatabaseResource
from pyalfred.contract.schema import AutoMarshmallowSchema
from pyalfred.server.utils import make_base_logger
from example.models import Base


def init_app():
    # ===== Database related ===== #
    engine = create_engine(
        os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///debug-database.db?check_same_thread=false"),
        **os.environ.get("SQLALCHEMY_ENGINE_OPTIONS", {"pool_pre_ping": True})
    )

    Session = scoped_session(sessionmaker(bind=engine))

    # ===== Initialize everything ===== #
    sleep(uniform(0., 5.))
    Base.metadata.create_all(bind=engine)

    api = Api()

    for base in AutoMarshmallowSchema.get_subclasses(Base):
        s = AutoMarshmallowSchema.generate_schema(base)
        api.add_route(f"/{s.endpoint()}", DatabaseResource(s, Session, create_ignore=["id"]))

    logger = make_base_logger(__name__)
    logger.info("Successfully registered all views")

    return api