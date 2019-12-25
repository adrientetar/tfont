import attr
from typing import Any, Dict, Optional


@attr.s(auto_attribs=True, cmp=False, repr=False, slots=True)
class Point:
    x: float
    y: float
    type: Optional[str] = None
    smooth: bool = False

    _extraData: Optional[Dict] = None

    _parent: Optional[Any] = attr.ib(default=None, init=False)
    selected: bool = attr.ib(default=False, init=False)

    def __repr__(self):
        if self.type is not None:
            more = ", %r" % self.type
            if self.smooth:
                more += ", smooth=%r" % self.smooth
        else:
            more = ""
        return "%s(%r, %r%s)" % (
            self.__class__.__name__, self.x, self.y, more)

    @property
    def extraData(self):
        extraData = self._extraData
        if extraData is None:
            extraData = self._extraData = {}
        return extraData

    @property
    def parent(self):
        return self._parent
