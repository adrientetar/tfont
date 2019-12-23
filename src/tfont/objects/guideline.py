import attr
from typing import Any, Optional, Union


@attr.s(cmp=False, repr=False, slots=True)
class Guideline(object):
    x: Union[int, float] = attr.ib()
    y: Union[int, float] = attr.ib()
    angle: Union[int, float] = attr.ib()
    name: str = attr.ib(default="")

    _parent: Optional[Any] = attr.ib(default=None, init=False)
    selected: bool = attr.ib(default=False, init=False)

    def __repr__(self):
        # name?
        return "%s(%r, %r, angle=%r)" % (
            self.__class__.__name__, self.x, self.y, self.angle)

    @property
    def parent(self):
        return self._parent
