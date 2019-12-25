import attr
from tfont.objects.misc import Matrix3x2
from typing import Any, Optional


@attr.s(auto_attribs=True, cmp=False, repr=False, slots=True)
class Component:
    glyphName: str
    transformation: Matrix3x2 = attr.Factory(Matrix3x2)

    _parent: Optional[Any] = attr.ib(default=None, init=False)
    selected: bool = attr.ib(default=False, init=False)

    def __repr__(self):
        return "%s(%r, %r)" % (
            self.__class__.__name__, self.glyphName, self.transformation)

    @property
    def glyph(self):
        try:
            return self._parent._parent._parent.glyphForName(self.glyphName)
        except (AttributeError, KeyError):
            pass

    @property
    def layer(self):
        layer = self._parent
        try:
            return layer._parent._parent.glyphForName(
                self.glyphName).layerForMaster(layer.masterName)
        except (AttributeError, KeyError):
            pass

    @property
    def origin(self):
        return self.transformation.transform(0, 0)

    @property
    def parent(self):
        return self._parent
