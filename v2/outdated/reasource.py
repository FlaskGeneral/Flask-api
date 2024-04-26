class Reasource(object):
    """
    All private variables and functions we use start with `_r_`. DO NOT EDIT THESE\n
    All public variables we use start with `r_`\n
    All other functions do not have a prefix
    """

    _r_methods = {}
    r_config = {}

    def add_method(self, method: str, view):
        """GET, PUT, PATCH, DELETE and POST are registered automatically if available"""
        self._r_methods[method, view]

    def configure(self, n, v):
        self.r_config[n] = v

    def _r_add_reasource(self):
        methods = ["GET", "PUT", "PATCH", "DELETE", "POST"]
        print("__dict__", self.__dict__)
        blueprint = f.Blueprint(type(self).__name__, type(self).__name__)
        for m in methods:
            try:
                print("METHOD")
                blueprint.route("/", methods=[m], view_func=self.__dict__[m])
            except:
                pass

        for k, v in self._r_methods.items():
            blueprint.route("/", methods=[k], view_func=v)
        return blueprint
