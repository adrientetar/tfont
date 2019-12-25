import attr
from typing import Any, Optional


@attr.s(auto_attribs=True, cmp=False, repr=False, slots=True)
class Guideline:
    x: float
    y: float
    angle: float
    name: str = ""

    _parent: Optional[Any] = attr.ib(default=None, init=False)
    selected: bool = attr.ib(default=False, init=False)

    def __repr__(self):
        # name?
        return "%s(%r, %r, angle=%r)" % (
            self.__class__.__name__, self.x, self.y, self.angle)

    @property
    def parent(self):
        return self._parent
