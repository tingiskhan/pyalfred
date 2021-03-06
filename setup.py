from setuptools import setup, find_packages
import os

NAME = "pyalfred"


def _get_version():
    folder = os.path.dirname(os.path.realpath(__file__))

    with open(os.path.join(folder, f"{NAME}/__init__.py"), "r") as f:
        versionline = next(line for line in f.readlines() if line.strip().startswith("__version__"))
        version = versionline.split("=")[-1].strip().replace('"', "")

    return version


setup(
    name=NAME,
    version=_get_version(),
    author="Victor Gruselius",
    author_email="victor.gruselius@gmail.com",
    description="Library for exposing SQLAlchemy models via REST in Falcon",
    packages=find_packages(include=(NAME, f"{NAME}.*")),
    install_requires=[
        "auto_schema @ git+https://github.com/tingiskhan/auto-schema#egg=auto_schema",
        "query-serializer @ git+https://github.com/tingiskhan/query-serializer#egg=query_serializer",
        "sqlalchemy",
        "starlette",
        "pyparsing",
    ],
)
