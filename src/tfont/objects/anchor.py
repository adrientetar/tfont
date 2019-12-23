import attr
from typing import Optional, Union


@attr.s(cmp=False, repr=False, slots=True)
class Anchor:
    x: Union[int, float] = attr.ib()
    y: Union[int, float] = attr.ib()
    name: str = attr.ib()

    _parent: Optional[object] = attr.ib(default=None, init=False)
    selected: bool = attr.ib(default=False, init=False)

    def __repr__(self):
        return "%s(%r, %r, %r)" % (
            self.__class__.__name__, self.name, self.x, self.y)

    @property
    def parent(self):
        return self._parent
