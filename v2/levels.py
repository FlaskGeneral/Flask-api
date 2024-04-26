import datetime as dt
from flask_sqlalchemy import SQLAlchemy as SQL
import sqlalchemy as sa
import datetime as dt

from . import errors as e, globals as g
import flask as f

db = g.db


class API_Key(db.Model):
    key = db.Column(sa.String(255), primary_key=True)
    level = db.Column(sa.String(255), nullable=False)
    logs = db.relationship("API_Key_Log", backref="api", lazy=True)
    __tablename__ = "api_key"

    def __repr__(self) -> str:
        return f"Key: {self.key}\nLevel: {self.level}\nLogs: {[l.__repr__() for l in self.logs]}"


class API_Key_Log(db.Model):
    __tablename__ = "api_key_log"
    key = db.Column(db.Integer, db.ForeignKey("api_key.key"), primary_key=True)
    action = db.Column(db.Text, nullable=False)
    when = db.Column(db.DateTime, default=dt.datetime.now(dt.UTC), nullable=False)
    status = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"Key: {self.key}\nAction:{self.action}\nWhen: {self.when}"


class Level:
    keys: list[API_Key] = []
    raw_keys: list = []

    def __init__(self, name) -> None:
        self.name = name

    def make_key_pass(
        self, uses: int, reset_seconds: int = None, reset_time: dt.datetime = None
    ):
        _type = "seconds" if reset_seconds else "time"
        reset = reset_seconds if reset_seconds else reset_time
        return Level_pass(uses, _type, self, reset)

    def new_key(self, key: str):
        k = API_Key(key=key, level=self.name)  # type: ignore
        l = API_Key_Log(api=k, action="Key Created")
        db.session.add_all([k, l])
        db.session.commit()
        self.keys.append(k)
        self.raw_keys.append(key)
        return key


class Level_pass:
    def __init__(self, uses, _type, level, reset) -> None:
        self.uses = uses
        self.type = _type
        self.level: Level = level
        self.reset = reset

    def request(self, key: str):
        k = self.level.raw_keys[self.level.raw_keys.index(key)]
        try:
            k.uses[self] += 1
        except:
            k.uses[self] = 0
        if self.uses < k.uses[self]:
            return {"status": "failed", "error": "Too many requests"}, 429
        else:
            return True

    def add_to_api(self, api):
        pass


class API_class:
    def __init__(self) -> None:
        self.levels = {}
        self.keys = {}

    def add_level(self, level: Level_pass):
        self.levels[level.level] = level
        level.add_to_api(self)

    def request(self, request: f.Request):
        key = request.headers.get("API_KEY")
        k = db.session.execute(db.select(API_Key).filter_by(key=key)).scalar()
        level = k.level
        l: Level = g.levels.levels[level]

        l_pass: Level_pass = self.levels[l]

        return l_pass.request(key)
