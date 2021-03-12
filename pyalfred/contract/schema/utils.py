from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.properties import ColumnProperty


def get_columns_of_object(base, prop_type=ColumnProperty):
    res = (c for c in vars(base).values() if isinstance(c, InstrumentedAttribute))

    if prop_type is None:
        return res

    return (c for c in res if isinstance(c.property, prop_type))


def find_col_types(base, type_):
    return [c for c in get_columns_of_object(base) if isinstance(c.property.columns[0].type, type_)]


def check_column_is_nullable(column: InstrumentedAttribute):
    if len(column.property.columns) != 1:
        raise ValueError(f"Can only handle when columns == 1!")

    return column.property.columns[-1].nullable
