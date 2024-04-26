from typing import Any


class Advanced_tuple(tuple):
    def __getattribute__(self, name: str) -> Any:
        for i in self:
            ret = []
            try:
                ret.append(getattr(i, name))
            except:
                pass
            return ret