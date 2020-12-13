from starlette.applications import Starlette
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
import os
from time import sleep
from numpy.random import uniform
from pyalfred.server.resources import DatabaseResource
from pyalfred.contract.schema import AutoMarshmallowSchema
from pyalfred.server.utils import make_base_logger
from .models import Base


def init_app():
    # ===== Database related ===== #
    engine = create_engine(
        os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///debug-database.db?check_same_thread=false"),
        **os.environ.get("SQLALCHEMY_ENGINE_OPTIONS", {"pool_pre_ping": True})
    )

    Session = scoped_session(sessionmaker(bind=engine))

    # ===== Initialize everything ===== #
    sleep(uniform(0.0, 1.0))
    Base.metadata.create_all(bind=engine)

    app = Starlette()

    for base in AutoMarshmallowSchema.get_subclasses(Base):
        s = AutoMarshmallowSchema.generate_schema(base)
        app.add_route(f"/{s.endpoint()}", DatabaseResource.make_endpoint(s, Session, create_ignore=["id"]))

    logger = make_base_logger(__name__)
    logger.info("Successfully registered all views")

    return app