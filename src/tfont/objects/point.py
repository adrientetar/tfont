import attr
from typing import Any, Dict, Optional, Union


@attr.s(cmp=False, repr=False, slots=True)
class Point:
    x: Union[int, float] = attr.ib()
    y: Union[int, float] = attr.ib()
    type: Optional[str] = attr.ib(default=None)
    smooth: bool = attr.ib(default=False)

    _extraData: Optional[Dict] = attr.ib(default=None)

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
