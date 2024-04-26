from typing import Any
from flask import current_app as app
from .api import API
from flask_sqlalchemy import SQLAlchemy as SQL


def app_api():
    return app.extensions["api"]


def refresh_globals():
    g = globals()
    g["current_api"] = app.extensions["api"]
    g["db"] = app.extensions.get("sqlalchemy", None)


class Proxy:
    def __getattribute__(self, name: str) -> Any:
        return Proxy()


class levels:
    items = {}

    def __setattr__(self, name: str, value: Any) -> None:
        self.items[name] = value


current_api: API = Proxy()
Levels = levels()
Levels.do = current_api.levels
Levels.levels = {}
db: SQL = Proxy()
