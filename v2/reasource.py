import typing as t
import flask as f
import pydantic as p
from pydantic import errors as pe, error_wrappers as pew
import json as j
from flask_sqlalchemy import SQLAlchemy as SQL
from sqlalchemy.sql import sqltypes as SQLt
from . import docs as d


class Reasource:
    def __init__(self, name, url="/") -> None:
        self.blueprint = f.Blueprint(name, name, url_prefix=url)
        self.__dict__["get"] = self.get
        self.__dict__["post"] = self.post
        self.__dict__["put"] = self.put

        self.help = []
        self.name = name

    def get(self, func, **options):
        def wrapper():
            self.blueprint.add_url_rule("/", view_func=func, methods=["GET"], **options)
            self.help.append(d.Method("GET", self.get))
            return func

        return wrapper

    def post(self, func, **options):
        def wrapper():
            self.blueprint.add_url_rule(
                "/", view_func=func, methods=["POST"], **options
            )
            self.help.append(d.Method("POST", self.post))
            return func

        return wrapper

    def put(self, func, **options):
        def wrapper():
            self.blueprint.add_url_rule("/", view_func=func, methods=["PUT"], **options)
            self.help.append(d.Method("PUT", self.put))

            return func

        return wrapper

    def patch(self, func, **options):
        def wrapper():
            self.blueprint.add_url_rule(
                "/", view_func=func, methods=["PATCH"], **options
            )
            self.help.append(d.Method("PATCH", self.patch))
            return func

        return wrapper

    def delete(self, func, **options):
        def wrapper():
            self.blueprint.add_url_rule(
                "/", view_func=func, methods=["DELETE"], **options
            )
            self.help.append(d.Method("DELETE", self.delete))
            return func

        return wrapper

    def method(self, func, method, help, **options):
        def wrapper():
            self.blueprint.add_url_rule(
                "/", view_func=func, methods=[method], **options
            )
            self.help.append(d.Method(method, self.method, help))
            return func

        return wrapper

    def load(self, api):
        pass


class Pydantic:
    """
    A subclass for recording instances
    """

    instances: dict[str, list] = {}

    def add(self, c: p.BaseModel):
        type_name = type(c).__name__
        try:
            self.instances[type_name].append(c)
        except KeyError:
            self.instances[type_name] = [c]
        return self

    def delete(self, c):
        type_name = type(c).__name__
        try:
            self.instances[type_name].remove(c)
        except TypeError:
            return False
        return True

    def sort(
        self, c, key: t.Union[str, None] = None, value: t.Any = None, filters: dict = {}
    ) -> list[p.BaseModel]:
        if key and value:
            filters[key] = value
        if filters == {}:
            print("FKV", filters, key, value)
            raise ValueError("key and value or filters must be set")

        instances = self.instances[c.__name__]
        for k, v in filters.items():
            ninstances = []
            for i in instances:
                if i.dict()[k] == int(v):
                    print(i.dict())
                    ninstances.append(i)
            instances = ninstances
        return ninstances


class Pydantic_route:
    def __init__(
        self,
        primary: str,
        c: p.BaseModel,
        rule: str,
        endpoint: t.Union[str, None] = None,
        provide_automatic_options: t.Union[bool, None] = None,
        func: t.Callable = None,
        name: str = None,
        **options: t.Any
    ) -> None:
        if not name:
            name = c.__name__
        self.name = name
        self.blueprint = f.Blueprint(name, name, url_prefix=rule)
        self.primary = primary
        self.c = c
        self.func = func
        options.pop("methods", None)
        self.methods = {
            "get": (d.NoBody("/<int:value>"),d.JSON(p.TypeAdapter(self.c).json_schema(), "/"),),
            "post": (d.JSON('{"status":"success"}', "/"),),
            "put": (d.JSON('{"status":"success"}', "/"), d.JSON('{"status":"success"}', "/<int:value>"),),
            "patch": (d.JSON('{"status":"success"}', "/<int:value>"),),
            "delete": (d.JSON('{"status":"success"}', "/<int:value>"),),
        }
        self.responces = {
            "get": [d.Responce(200, p.TypeAdapter(self.c).json_schema())],
            "post": [d.Responce(200 ,'{"status":"success"}')],
            "put": [d.Responce(200 ,'{"status":"success"}')],
            "patch": [d.Responce(200 ,'{"status":"success"}')],
            "delete": [d.Responce(200 ,'{"status":"success"}')],
        }
        self.views = {
            "get": self.get,
            "post": self.post,
            "patch": self.patch,
            "delete": self.delete,
            "put": self.put,
        }
        self.help = []
        for method,v in self.methods.items():
            mimes = []
            for url in v:
                mimes.append(d.MIME(self,url,self.responces[method]))
            self.help.append(d.Method(method, self.views[method], *mimes))

        self.routing = {
            "endpoint": endpoint,
            "provide_automatic_options": provide_automatic_options,
            "options": options,
        }

    def get(self, value=None):
        api = self.api
        pydantic: Pydantic = api.pydantic
        if f.request.content_type == "application/json":
            data = pydantic.sort(self.c, f.request.json)
        else:
            data = pydantic.sort(self.c, self.primary, value)
       
        ndata = []
        for i in data:
            ndata.append(i.dict())
        if self.func != None:
            self.func(method="GET", c=data, request=f.request)
        return ndata, 200

    def post(self):
        try:
            c = self.c.validate(f.request.json)
            self.api.pydantic.add(c)
            if self.func != None:
                self.func(method="POST", c=c, request=f.request)
            return {"status": "success"}, 200
        except p.ValidationError as e:
            error = j.loads(e.json())
            message = f.jsonify({"status": "failed", "error": error})
            return message, 422

    def put(self, value=None):
        try:
            if value != f.request.json.get(self.primary, None):
                raise p.ValidationError(
                    [
                        pew.ErrorWrapper(
                            ValueError("Primary keys must match"), self.primary
                        )
                    ],
                    self.c,
                )
            if not value:
                if not f.request.json.get(self.primary, None):
                    raise p.ValidationError(
                        [
                            pew.ErrorWrapper(
                                ValueError("Primary key must be set"), self.primary
                            )
                        ],
                        self.c,
                    )
                else:
                    value = f.request.json.get(self.primary)
            old = self.api.pydantic.sort(self.c, self.primary, value)[-1]
            self.api.pydantic.delete(old)
            data = j.load(old.json()).update(f.request.json)
            c = self.c.validate(data)
            self.api.pydantic.add(c)
            if self.func != None:
                self.func(method="PUT", c=c, old=old, request=f.request)
            return {"status": "success", "value": x}, 200
        except p.ValidationError as e:
            error = j.loads(e.json())
            message = f.jsonify({"status": "failed", "error": error})
            return message, 422

    def patch(self, value):
        pydantic: Pydantic = self.api.pydantic
        json = f.request.json
        c: p.BaseModel = pydantic.sort(self.c, self.primary, value)[-1]
        old = c
        for k, v in json.items():
            c.__dict__[k] = v
        if self.func != None:
            self.func(method="PATCH", c=c, old=old, request=f.request, json=json)
        return {"status": "success"}, 200

    def delete(self, value):
        pydantic: Pydantic = self.api.pydantic
        c = pydantic.sort(self.c, self.primary, value)
        pydantic.delete(c)
        if self.func != None:
            self.func(method="DELETE", c=c, request=f.request)
        return {"status": "success"}, 200

    def load_to_api(self, group, api):
        self.api = api
        b: f.Blueprint = group.blueprint

        options = self.routing.pop("options", {})
        for k, v in self.methods.items():
            for m in v:
                self.blueprint.add_url_rule(
                    **self.routing,
                    rule=m.url,
                    methods=[k],
                    view_func=self.views[k],
                    **options
                )
        b.register_blueprint(self.blueprint)


class SQL_route:
    def __init__(
        self,
        c,
        rule: str,
        key: str,
        endpoint: t.Union[str, None] = None,
        provide_automatic_options: t.Union[bool, None] = None,
        func: t.Callable = None,
        name: str = None,
        **options: t.Any
    ) -> None:
        if not name:
            name = c.__tablename__
        self.name = name
        #self.__config__ 
        self.blueprint = f.Blueprint(name, name, url_prefix=rule)
        self.c = c
        self.func = func
        self.key = key
        options.pop("methods", None)
        self.methods = {
            "get": (d.NoBody("/<int:value>"),d.JSON('{}', "/"),),
            "post": (d.JSON('{"status":"success"}', "/"),),
            "put": (d.JSON('{"status":"success"}', "/"), d.JSON('{"status":"success"}', "/<int:value>"),),
            "patch": (d.JSON('{"status":"success"}', "/<int:value>"),),
            "delete": (d.JSON('{"status":"success"}', "/<int:value>"),),
        }
        self.responces = {
            "get": [d.Responce(200, '{}')],
            "post": [d.Responce(200 ,'{"status":"success"}')],
            "put": [d.Responce(200 ,'{"status":"success"}')],
            "patch": [d.Responce(200 ,'{"status":"success"}')],
            "delete": [d.Responce(200 ,'{"status":"success"}')],
        }

        self.views = {
            "get": self.get,
            "post": self.post,
            "patch": self.patch,
            "delete": self.delete,
            "put": self.put,
        }
        self.help = []
        for method,v in self.methods.items():
            mimes = []
            for url in v:
                mimes.append(d.MIME(self, url, self.responces[method]))
            self.help.append(d.Method(method, self.views[method], *mimes))


        self.types = {
            SQLt.String: (str, pe),
            SQLt.Integer: (int, pe),
            SQLt.BOOLEAN: (bool, pe),
            SQLt.Boolean: (bool, pe),
        }
        self.routing = {
            "endpoint": endpoint,
            "provide_automatic_options": provide_automatic_options,
            "options": options,
        }

    def get(self, value=None):
        if f.request.content_type == "application/json":
            i = f.request.json
            data = self.db.session.execute(self.db.select(self.c).filter_by(**i))
            json = []
            for r in data:
                row = {}
                for k, v in r:
                    row[k] = v
                json.append(row)
            return json, 200
        else:
            if value ==  None:
                f.abort(415)
            i = {str(self.key): int(value)}
            data = self.db.session.execute(self.db.select(self.c).filter_by(**i)).one()
            data_dict = data[0].__dict__
            data_dict.pop("_sa_instance_state")
            return data_dict, 200

    def post(self):
        try:
            json = f.request.json
            for c in self.c.__table__._columns:
                if c.name in json.keys():
                    error = self.types[type(c.type)]
                    if error[0] != type(json[c.name]):
                        raise p.ValidationError(
                            [pew.ErrorWrapper(error[1](), c.name)], self.c
                        )
            self.db.session.add(self.c(**json))
            self.db.session.commit()
            return {"status": "success"}
        except p.ValidationError as e:
            error = j.loads(e.json())
            message = f.jsonify({"status": "failed", "error": error})
            return message, 422

    def put(self):
        json = f.request.json
        i = {str(self.key): json.get(self.key)}
        self.db.session.delete(
            self.db.session.execute(self.db.select(self.c).filter_by(**i))
        )
        return self.post()

    def delete(self, value):
        if f.request.content_type == "application/json":
            value = f.request.json.get(self.key)
        i = {str(self.key): value}
        self.db.session.delete(
            self.db.session.execute(self.db.select(self.c).filter_by(**i))
        )

    def patch(self, value):
        try:
            json = f.request.json
            if str(value) != str(json.get(self.key, None)):
                print(value, json.get(self.key, None))
                print(type(value), type(json.get(self.key, None)))
                print(value == json.get(self.key, None))
                raise p.ValidationError(
                    [pew.ErrorWrapper(ValueError("Primary keys must match"), self.key)],
                    self,
                )
            if not value:
                if not json.get(self.key, None):
                    raise p.ValidationError(
                        [
                            pew.ErrorWrapper(
                                ValueError("Primary key must be set"), self.key
                            )
                        ],
                        self,
                    )
                else:
                    value = json.get(self.key)
            i = {str(self.key): value}
            cl = self.db.session.execute(self.db.select(self.c).filter_by(**i)).scalar()
            for c in self.c.__table__._columns:
                if c.name in json.keys():
                    error = self.types[type(c.type)]
                    if error[0] != type(json[c.name]):
                        raise p.ValidationError(
                            [pew.ErrorWrapper(error[1](), c.name)], self
                        )
                    else:
                        cl.__setattr__(c.name, json.get(c.name))
                        self.db.session.commit()
            return {"status": "success"}
        except p.ValidationError as e:
            error = j.loads(e.json())
            message = f.jsonify({"status": "failed", "error": error})
            return message, 422

    def all(self):
        data = self.db.session.execute(self.db.select(self.c))
        json = []
        for r in data:
            data_dict = r[0].__dict__
            data_dict.pop("_sa_instance_state")
            json.append(data_dict)
        return json, 200

    def clear(self):
        r = self.db.session.execute(self.db.select(self.c)).scalars()
        l = 0
        for c in r:
            l += 1
            self.db.session.delete(c)
        self.db.session.commit()
        return {"status": "success", "number": l}

    def load_to_api(self, group, api):
        self.api = api
        self.db: SQL = f.current_app.extensions.get("sqlalchemy", None)
        if not isinstance(self.db, SQL):
            raise ValueError(
                "SQLAlchemy table has been added but no flask_sqlalchemy class exists"
            )
        b: f.Blueprint = group.blueprint
        options = self.routing.pop("options", {})
        self.blueprint.add_url_rule(
            **self.routing, rule="/all", methods=["GET"], view_func=self.all, **options
        )
        self.blueprint.add_url_rule(
            **self.routing,
            rule="/clear",
            methods=["DELETE"],
            view_func=self.clear,
            **options
        )
        for k, v in self.methods.items():
            for m in v:
                self.blueprint.add_url_rule(
                    **self.routing,
                    rule=m.url,
                    methods=[k],
                    view_func=self.views[k],
                    **options
                )
        b.register_blueprint(self.blueprint)
