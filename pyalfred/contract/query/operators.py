from operator import eq, le, lt, ge, gt, ne, and_, or_
from collections import OrderedDict

OPERATOR_MAP = {"==": eq, "<=": le, "<": lt, ">=": ge, ">": gt, "!=": ne}
ASSOC_OPERATOR = OrderedDict({"AND": and_, "OR": or_})

INVERSE_OPERATOR_MAP = {v: k for k, v in OPERATOR_MAP.items()}
INVERSE_ASSOC_OPERATOR_MAP = {v: k for k, v in ASSOC_OPERATOR.items()}
