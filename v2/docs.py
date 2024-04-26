import flask as f
import typing as t
import json as j
from . import utils as u

METHOD_HTML = '''
            <div id="{method.name}" class="method">
            <button class="method"  style="display:block;" onclick="showhide({method.name}, {method} )">
                    <div>
                        <h2>{method.name}</h2>
                        {# <button onclick="showhide('{method.name}')">Show</button> #}
                    </div>
                </button>
            <select  id="select {method.name}" onchange="changetype( {method.name}, this)">
'''
SELECT_HTML = '''
                    <option value="{type}">{type}</option>
'''
METHOD_HTML_2 = '''</select>'''
MIME_HTML = '''
                <div id="doc {mime.type}" style="display: none;">
                    <h3>Help</h3>
                    <p>{method.help}</p>
                    <div id="{mime.type}">
'''
INPUT_HTML = '''
                        <input type="{input.type}}"/>
'''
METHOD_HTML_3 = '''
                <button onclick="test_api({method})">Test</button>
                    </div>
                </div>
'''


class JSON:
    def __init__(self, example, url) -> None:
        self.example = example
        self.type = "application/json"
        self.url = url
    #    self.JSON = j.dumps(self.__dict__)

class NoBody:
    """
    Url should be a list. Variable endpoints should be surrounded in curly brackets/braces {}.
    Example: ["api", "reasource", "{id}"] would be equal to api/reasource/<id> in a flask route
    """

    def __init__(self, url) -> None:
        self.url = url
        self.type = "no-body"
    #    self.JSON = j.dumps(self.__dict__)



class Responce:
    def __init__(self, code, example) -> None:
        self.code = code
        self.example = example


class MIME:
    def __init__(self, reasource, example_request:t.Union[JSON, NoBody], responce: list[Responce]) -> None:
        self.reasource = reasource
        self.type = example_request.type
        self.example_request = example_request
        self.responces = responce

class Method:
    def __init__(self, name, func, *mimes: MIME, **options) -> None:
        self.name = name
        self.func = func
        self.endpoint: str
        self.types = u.Advanced_tuple(mimes).type
        self.mimes = mimes


class Doc:
    def __init__(self, app) -> None:
        self.blueprint = f.Blueprint(
            "docs", "docs", template_folder="v2\\templates\\docs", url_prefix="/docs"
        )
        self.docs = "docs.html"
        self.app = app
        self.reasources = []

    def add_reasource(
        self, 
        reasource,
    ):
        self.reasources.append(reasource)

    def add_to_web(self):
        for r in self.reasources:

            def web():
                return f.render_template(self.docs, reasource=r, app=self.app)

            for re in r.help:
                re: Method
                endpoint = list(f.current_app.view_functions.keys())[
                    list(f.current_app.view_functions.values()).index(re.func)
                ]
                re.endpoint = endpoint
            self.blueprint.add_url_rule(f"/{r.name}", r.name, web)
