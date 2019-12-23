import attr
from tfont.objects.layer import Layer
from tfont.objects.misc import observable_list
from typing import Any, Dict, List, Optional, Tuple


@attr.s(cmp=False, repr=False, slots=True)
class Glyph:
    name: str = attr.ib()
    unicodes: List[str] = attr.ib(default=attr.Factory(list))

    leftKerningGroup: str = attr.ib(default="")
    rightKerningGroup: str = attr.ib(default="")
    bottomKerningGroup: str = attr.ib(default="")
    topKerningGroup: str = attr.ib(default="")

    _layers: List[Layer] = attr.ib(default=attr.Factory(list))

    # Color format: RGBA8888.
    color: Optional[Tuple[int, int, int, int]] = attr.ib(default=None)
    _extraData: Optional[Dict] = attr.ib(default=None)

    _parent: Optional[Any] = attr.ib(default=None, init=False)
    selected: bool = attr.ib(default=False, init=False)

    def __attrs_post_init__(self):
        for layer in self._layers:
            layer._parent = self

    def __repr__(self):
        return "%s(%r, %d layers)" % (
            self.__class__.__name__, self.name, len(self._layers))

    @property
    def extraData(self):
        extraData = self._extraData
        if extraData is None:
            extraData = self._extraData = {}
        return extraData

    @property
    def font(self):
        return self._parent

    @property
    def layers(self):
        return observable_list(self, self._layers)

    @property
    def unicode(self):
        unicodes = self.unicodes
        if unicodes:
            return unicodes[0]
        return None

    def layerForMaster(self, master):
        if master is None:
            font = self._parent
            if font is not None:
                name = font.selectedMaster.name
            else:
                raise ValueError("unreachable fallback master")
        elif master.__class__ is str:
            name = master
        else:
            name = master.name
        layers = self._layers
        for layer in layers:
            if not layer._name and layer.masterName == name:
                return layer
        layer = Layer(masterName=name)
        layer._parent = self
        layers.append(layer)
        return layer
