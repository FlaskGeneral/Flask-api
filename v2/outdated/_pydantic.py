import pydantic as p
import pandas as pd


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
        return self

    def sort(self, c, **filter):
        df = pd.DataFrame(self.instances[c])
        fdf = df
        for k, v in filter.items():
            fdf = fdf.loc[df[k] == v]
        return fdf


if __name__ == "__main__":

    class Py(p.BaseModel):
        name: str
        description: str | None = None
        price: float
        tax: float | None = None

    y = Py(name="", price=123)
    x = Pydantic().add(y)
    print(x.instances)
    x.delete(y)
    print(x.instances)
