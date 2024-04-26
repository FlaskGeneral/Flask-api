import flask as f
from . import reasource as r
import typing as t


class Group:
    def __init__(self, name, import_name, url="/") -> None:
        self.blueprint = f.Blueprint(name, import_name, url_prefix=url)
        self.pydantic = []
        self.sql = []
        self.all_reasources = []

    def add_reasource(self, reasource: r.Reasource, **options):
        blueprint = reasource.blueprint
        self.all_reasources.append(reasource)
        self.blueprint.register_blueprint(blueprint, **options)

    def add_pydantic(self, c, primary_key, url, edit_func=None):
        x = r.Pydantic_route(primary_key, c, url, func=edit_func)
        self.pydantic.append(x)
        self.all_reasources.append(x)

    def add_SQL(self, c, url, primary_key):
        x = r.SQL_route(c, url, key=primary_key)
        self.sql.append(x)
        self.all_reasources.append(x)

    def add_pass(self, api_pass):
        a = api_pass

        @self.blueprint.before_request
        def api_key():
            r = a.request(f.request)
            if r != True:
                return r

    def _add(self, api):
        for p in self.pydantic:
            p.load_to_api(self, api)
        for s in self.sql:
            s.load_to_api(self, api)
