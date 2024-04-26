import flask as f
from . import group as g, globals, reasource as r, docs as d
import typing as t
from flask_sqlalchemy import SQLAlchemy as SQL


class API:
    def __init__(
        self,
        name,
        import_name,
        subdomain: str = None,
        app: f.Flask = None,
        blueprint: f.Blueprint = None,
        levels: bool = False,
        url_prefix="/api",
    ) -> None:
        self.blueprint = blueprint or f.Blueprint(
            name, import_name, subdomain=subdomain, url_prefix=url_prefix
        )
        self.levels = False
        self.pydantic = r.Pydantic()
        self.levels = levels
        self.docs = d.Doc(self)
        if app != None:
            self.init_app(app)

    def init_app(self, app: f.Flask):
        with app.app_context():
            app.extensions["api"] = self

            @app.before_request
            def refresh_app():
                globals.refresh_globals()

            globals.refresh_globals()

        @self.blueprint.route("/static/<path:filename>")
        def API_Static(filename):
            return f.send_from_directory(".\\v2\\static", filename)

    def load(self, app: f.Flask):
        if not isinstance(app, f.Flask) and self.docs:
            raise TypeError(
                "Docs can only work when the API is directly atatched to the instance"
            )
        app.register_blueprint(self.blueprint)
        self.docs.add_to_web()
        app.register_blueprint(self.docs.blueprint)

    def add_group(self, *groups: g.Group):
        for group in groups:
            group._add(self)
            for r in group.all_reasources:
                self.docs.add_reasource(r)
            self.blueprint.register_blueprint(group.blueprint)
