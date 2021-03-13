from models import Base
import os
from pyalfred.server.utils import make_base_logger
from sqlalchemy import create_engine


if __name__ == "__main__":
    logger = make_base_logger(__name__)
    logger.info("Running database initialization scripts")

    url = os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///debug-database.db?check_same_thread=false")
    engine = create_engine(url, **os.environ.get("SQLALCHEMY_ENGINE_OPTIONS", {"pool_pre_ping": True}), )

    Base.metadata.create_all(bind=engine)
    logger.info("Created tables")
