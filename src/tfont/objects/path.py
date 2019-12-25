import attr
import pprint
from tfont.objects.misc import observable_list
from tfont.objects.point import Point
from typing import Any, Dict, List, Optional


@attr.s(auto_attribs=True, cmp=False, repr=False, slots=True)
class Path:
    _points: List[Point] = attr.Factory(list)

    _extraData: Optional[Dict] = None

    _parent: Optional[Any] = attr.ib(default=None, init=False)

    def __attrs_post_init__(self):
        for point in self._points:
            point._parent = self

    def __bool__(self):
        return bool(self._points)

    def __repr__(self):
        name = self.__class__.__name__
        width = 80 - len(name) - 2
        return "%s(%s)" % (
            name, pprint.pformat(self._points, width=width).replace(
                "\n ", "\n  " + " " * len(name)))  # pad indent

    @property
    def extraData(self):
        extraData = self._extraData
        if extraData is None:
            extraData = self._extraData = {}
        return extraData

    @property
    def parent(self):
        return self._parent

    @property
    def points(self):
        return observable_list(self, self._points)

    def transform(self, matrix, selectionOnly=False):
        for point in self._points:
            if not selectionOnly or point.selected:
                point.x, \
                point.y = matrix.transform(point.x, point.y)
