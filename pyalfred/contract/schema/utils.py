from sqlalchemy.orm.attributes import InstrumentedAttribute


def find_col_types(base, type_):
    return [
        c
        for c in vars(base).values()
        if isinstance(c, InstrumentedAttribute) and isinstance(c.property.columns[0].type, type_)
    ]


def check_column_is_nullable(column: InstrumentedAttribute):
    if len(column.property.columns) != 1:
        raise ValueError(f"Can only handle when columns == 1!")

    return column.property.columns[-1].nullable