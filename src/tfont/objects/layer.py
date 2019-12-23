import attr
from tfont.objects.anchor import Anchor
from tfont.objects.component import Component
from tfont.objects.guideline import Guideline
from tfont.objects.misc import Transformation, observable_list
from tfont.objects.path import Path
from typing import Any, Dict, List, Optional, Tuple, Union


@attr.s(cmp=False, repr=False, slots=True)
class Layer:
    masterName: str = attr.ib(default="")
    _name: str = attr.ib(default="")
    location: Optional[Dict[str, int]] = attr.ib(default=None)

    width: Union[int, float] = attr.ib(default=600)
    # should default to ascender+descender and only be stored if different from
    # that value -- add a None value for it and a property?
    height: Union[int, float] = attr.ib(default=0)
    yOrigin: Optional[Union[int, float]] = attr.ib(default=None)

    _anchors: List[Anchor] = attr.ib(default=attr.Factory(list))
    _components: List[Component] = attr.ib(default=attr.Factory(list))
    _guidelines: List[Guideline] = attr.ib(default=attr.Factory(list))
    _paths: List[Path] = attr.ib(default=attr.Factory(list))

    # Color format: RGBA8888.
    color: Optional[Tuple[int, int, int, int]] = attr.ib(default=None)
    _extraData: Optional[Dict] = attr.ib(default=None)

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
            self.__class__.__name__, self.name, len(self._paths), more)

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
        self.transform(Transformation(xOffset=delta))
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
    def name(self):
        if self.masterLayer:
            return self.master.name
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

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
