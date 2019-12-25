import attr
from typing import Any, Optional


@attr.s(auto_attribs=True, cmp=False, repr=False, slots=True)
class Anchor:
    x: float
    y: float
    name: str

    _parent: Optional[Any] = attr.ib(default=None, init=False)
    selected: bool = attr.ib(default=False, init=False)

    def __repr__(self):
        return "%s(%r, %r, %r)" % (
            self.__class__.__name__, self.name, self.x, self.y)

    @property
    def parent(self):
        return self._parent
