import unittest
from pyalfred.contract.query import QueryBuilder
from test.model import Task
from datetime import date


class QueryTest(unittest.TestCase):
    def test_QueryToString(self):
        qb = QueryBuilder(Task)

        expr = Task.name == "Test"

        expected = "(name == \"Test\")"
        as_string = qb.to_string(expr)

        self.assertEqual(expected, as_string)

    def test_QueryToStringMultipleFiltration(self):
        qb = QueryBuilder(Task)

        date_ = date.today()
        expr = (Task.name == "Test") & (Task.finished_by < date_)

        expected = f"((name == \"Test\") AND (finished_by < {date_:%Y-%m-%d}))"
        as_string = qb.to_string(expr)

        self.assertEqual(expected, as_string)


if __name__ == '__main__':
    unittest.main()
