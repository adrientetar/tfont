import attr
from typing import Any, Optional


@attr.s(auto_attribs=True, cmp=False, repr=False, slots=True)
class Axis:
    tag: str
    min: int = 0
    max: int = 0
    default: int = 0
    name: str = ""

    _parent: Optional[Any] = attr.ib(default=None, init=False)

    def __repr__(self):
        return "%s(%r, [%d:%d:%d])" % (
            self.__class__.__name__, self.tag, self.min, self.default,
            self.max)

    @property
    def parent(self):
        return self._parent
