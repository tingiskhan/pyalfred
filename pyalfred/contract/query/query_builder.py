import pyparsing as pp
from sqlalchemy import bindparam
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList
from sqlalchemy.ext.declarative import DeclarativeMeta
from typing import Union, Type
from .operators import OPERATOR_MAP, INVERSE_OPERATOR_MAP, ASSOC_OPERATOR, INVERSE_ASSOC_OPERATOR_MAP
from ...constants import STRING_SYMBOL
from ..schema import AutoMarshmallowSchema


# Adapted from: https://stackoverflow.com/questions/11133339/parsing-a-complex-logical-expression-in-pyparsing-in-a-binary-tree-fashion
class QueryBuilder(object):
    def __init__(self, obj: Type[DeclarativeMeta]):
        """
        Class for building a BinaryExpression from string, or vice versa.
        :param obj: The object
        """

        self._obj = obj
        self._parser = self._build_parser()
        self._schema = AutoMarshmallowSchema.get_schema(obj)

    @staticmethod
    def _build_parser():
        operator = pp.Regex("|".join(OPERATOR_MAP.keys())).setName("operator")
        comparison_term = (
            pp.pyparsing_common.iso8601_datetime.copy()
            | pp.pyparsing_common.iso8601_date.copy()
            | pp.pyparsing_common.number.copy()
            | pp.QuotedString(STRING_SYMBOL)    # Strings and enums
            | pp.Word(pp.alphas)                # Enums
        )

        condition = pp.Group(pp.pyparsing_common.identifier + operator + comparison_term)

        return pp.operatorPrecedence(condition, [(k, 2, pp.opAssoc.LEFT) for k in ASSOC_OPERATOR])

    def _recursion(self, expr: pp.ParseResults) -> Union[BinaryExpression, BooleanClauseList]:
        if len(expr) != 3:
            raise ValueError("Something went wrong when parsing, cannot be more than three elements!")

        if not isinstance(expr[0], pp.ParseResults):
            attr = getattr(self._obj, expr[0])
            value = self._schema(only=[attr.name]).load({attr.name: expr[2]})[attr.name]

            return BinaryExpression(attr, bindparam(None, value, type_=attr.type), OPERATOR_MAP[expr[1]])

        left = self._recursion(expr[0])
        right = self._recursion(expr[-1])
        operator = expr[1]

        return ASSOC_OPERATOR[operator](left, right)

    def to_string(self, expression: Union[BooleanClauseList, BinaryExpression]):
        if isinstance(expression, BooleanClauseList):
            left = self.to_string(expression.clauses[0])
            right = self.to_string(expression.clauses[1])

            return f"{left}{INVERSE_ASSOC_OPERATOR_MAP[expression.operator]}{right}"

        left = expression.left.name

        if issubclass(expression.left.type.python_type, bool):
            value = str(expression.right)
        else:
            value = expression.right.value

        right = self._schema(only=[left]).dump({left: value})[left]

        if issubclass(getattr(self._obj, expression.left.name).type.python_type, str):
            right = f"{STRING_SYMBOL}{right}{STRING_SYMBOL}"

        return f"{left}{INVERSE_OPERATOR_MAP[expression.operator]}{right}"

    def from_string(self, expression: str):
        root = self._parser.parseString(expression)[0]

        return self._recursion(root)
