from starlette.applications import Starlette
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
import os
from pyalfred.server import DatabaseResource
from pyalfred.contract.client import Client
from auto_schema import AutoMarshmallowSchema
from pyalfred.server.utils import make_base_logger
from models import Base


def init_app():
    engine = create_engine(
        os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///debug-database.db?check_same_thread=false"),
        **os.environ.get("SQLALCHEMY_ENGINE_OPTIONS", {"pool_pre_ping": True}),
    )

    Session = scoped_session(sessionmaker(bind=engine))
    app = Starlette()

    logger = make_base_logger(__name__)

    for base in AutoMarshmallowSchema.get_subclasses(Base):
        s = AutoMarshmallowSchema.generate_schema(base)
        endpoint = Client.make_endpoint(s)

        logger.info(f"Registering '{endpoint}'")
        app.add_route(f"/{endpoint}", DatabaseResource.make_endpoint(s, Session, create_ignore=["id"]))

    logger.info("Successfully registered all views")
    logger.info(f"Registered routes: {', '.join(r.path for r in app.routes)}")

    return app
