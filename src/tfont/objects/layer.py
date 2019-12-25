import attr
from tfont.objects.anchor import Anchor
from tfont.objects.component import Component
from tfont.objects.guideline import Guideline
from tfont.objects.misc import Matrix3x2, observable_list
from tfont.objects.path import Path
from typing import Any, Dict, List, Optional, Tuple, Union


@attr.s(auto_attribs=True, cmp=False, repr=False, slots=True)
class Layer:
    masterName: str = ""
    name: str = ""
    location: Optional[Dict[str, int]] = None

    width: Union[int, float] = 600
    # should default to ascender+descender and only be stored if different from
    # that value -- add a None value for it and a property?
    height: Union[int, float] = 0
    yOrigin: Optional[Union[int, float]] = None

    _anchors: List[Anchor] = attr.Factory(list)
    _components: List[Component] = attr.Factory(list)
    _guidelines: List[Guideline] = attr.Factory(list)
    _paths: List[Path] = attr.Factory(list)

    # Color format: RGBA8888.
    color: Optional[Tuple[int, int, int, int]] = None
    _extraData: Optional[Dict] = None

    _parent: Optional[Any] = attr.ib(default=None, init=False)

    def __attrs_post_init__(self):
        for anchor in self._anchors:
            anchor._parent = self
        for component in self._components:
            component._parent = self
        for guideline in self._guidelines:
            guideline._parent = self
        for path in self._paths:
            path._parent = self

    def __bool__(self):
        return bool(self._paths or self._components)

    # add __lt__ to display layers ordered

    def __repr__(self):
        try:
            more = ", glyph %r%s" % (
                self._parent.name, " master" * self.masterLayer)
        except AttributeError:
            more = ""
        return "%s(%r, %d paths%s)" % (
            self.__class__.__name__, self.displayName, len(self._paths), more)

    @property
    def anchors(self):
        return observable_list(self, self._anchors)

    @property
    def bottomMargin(self):
        bounds = self.bounds
        if bounds is not None:
            value = bounds[1]
            if self.yOrigin is not None:
                value -= self.yOrigin - self.height
            return value
        return None

    @bottomMargin.setter
    def bottomMargin(self, value):
        bounds = self.bounds
        if bounds is None:
            return
        oldValue = bounds[1]
        if self.yOrigin is not None:
            oldValue -= self.yOrigin - self.height
        else:
            self.yOrigin = self.height
        self.height += value - oldValue

    @property
    def components(self):
        return observable_list(self, self._components)

    @property
    def displayName(self):
        if self.masterLayer:
            return self.master.name
        return self._name

    @property
    def extraData(self):
        extraData = self._extraData
        if extraData is None:
            extraData = self._extraData = {}
        return extraData

    @property
    def guidelines(self):
        return observable_list(self, self._guidelines)

    @property
    def leftMargin(self):
        bounds = self.bounds
        if bounds is not None:
            return bounds[0]
        return None

    @leftMargin.setter
    def leftMargin(self, value):
        bounds = self.bounds
        if bounds is None:
            return
        delta = value - bounds[0]
        self.transform(Matrix3x2.create_translation(delta, 0))
        self.width += delta

    @property
    def master(self):
        try:
            return self._parent._parent._masters[self.masterName]
        except (AttributeError, KeyError):
            pass
        return None

    @property
    def masterLayer(self):
        return self.masterName and not self._name

    @property
    def parent(self):
        return self._parent

    @property
    def paths(self):
        return observable_list(self, self._paths)

    @property
    def rightMargin(self):
        bounds = self.bounds
        if bounds is not None:
            return self.width - bounds[2]
        return None

    @rightMargin.setter
    def rightMargin(self, value):
        bounds = self.bounds
        if bounds is None:
            return
        self.width = bounds[2] + value

    @property
    def topMargin(self):
        bounds = self.bounds
        if bounds is not None:
            value = -bounds[3]
            if self.yOrigin is not None:
                value += self.yOrigin
            else:
                value += self.height
            return value
        return None

    @topMargin.setter
    def topMargin(self, value):
        bounds = self.bounds
        if bounds is None:
            return
        top = bounds[3]
        oldValue = -top
        if self.yOrigin is not None:
            oldValue += self.yOrigin
        else:
            oldValue += self.height
        self.yOrigin = top + value
        self.height += value - oldValue

    def transform(self, matrix, selectionOnly=False):
        for anchor in self._anchors:
            if not selectionOnly or anchor.selected:
                anchor.x, \
                anchor.y = matrix.transform(anchor.x, anchor.y)
        for component in self._components:
            if not selectionOnly or component.selected:
                component.transformation *= matrix
        for guideline in self._guidelines:
            if not selectionOnly or guideline.selected:
                guideline.x, \
                guideline.y = matrix.transform(guideline.x, guideline.y)
        for path in self._paths:
            path.transform(matrix, selectionOnly)
