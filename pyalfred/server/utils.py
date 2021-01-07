import logging
from typing import Sequence
from sqlalchemy.orm import Query


def make_base_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(name)s: %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.setLevel(logging.DEBUG)

    return logger


# TODO: Do better
def apply_filter_from_string(model, query: Query, filters: Sequence[str]):
    for f in filters:
        as_lower = f.lower()

        if f == "":
            pass

        elif as_lower.startswith("order by"):
            attribute_name = as_lower.replace("order by", "")

            descending = False
            if attribute_name.endswith("desc") or attribute_name.endswith("descending"):
                descending = True

                if attribute_name.endswith("desc"):
                    attribute_name = attribute_name.replace("desc", "")
                else:
                    attribute_name = attribute_name.replace("descending", "")

            to_order_on = getattr(model, attribute_name.strip())

            if descending:
                to_order_on = to_order_on.desc()

            query = query.order_by(to_order_on)

        elif as_lower == "first":
            return query.first()

        elif as_lower.startswith("limit"):
            to_limit = as_lower.replace("limit", "")
            query = query.limit(int(to_limit.strip()))

        else:
            raise NotImplementedError(f"Have not implemented filter: {f}")

    return query.all()
