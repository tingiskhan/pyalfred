from sqlalchemy import Enum, LargeBinary
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from functools import lru_cache
from typing import Type
from sqlalchemy.ext.declarative import DeclarativeMeta
from .utils import find_col_types
from .handlers import EnumHandler, BytesFieldHandler


@classmethod
def endpoint(cls):
    return cls.__name__.lower().replace("schema", "")


_CUSTOM_HANDLING = {Enum: EnumHandler(), LargeBinary: BytesFieldHandler}


class AutoMarshmallowSchema(SQLAlchemyAutoSchema):
    @classmethod
    @lru_cache(maxsize=100)
    def generate_schema(cls, base_class: DeclarativeMeta):
        state_dict = {"Meta": type("Meta", (object,), {"model": base_class, "include_fk": True}), "endpoint": endpoint}

        # ===== Custom converters ===== #
        for column_type, handler in _CUSTOM_HANDLING.items():
            columns_of_type = find_col_types(base_class, column_type)

            for column in columns_of_type:
                handler(column, state_dict)

        return type(f"{base_class.__name__}Schema", (AutoMarshmallowSchema,), state_dict)

    @classmethod
    def get_schema(cls, obj: Type):
        return cls.generate_schema(obj)

    @classmethod
    def get_subclasses(cls, base):
        res = base.__subclasses__()

        for e in res:
            res.extend(cls.get_subclasses(e))

        return res
