import attr
from tfont.objects.guideline import Guideline
from tfont.objects.misc import AlignmentZone, observable_list
from typing import Any, Dict, List, Optional


@attr.s(cmp=False, repr=False, slots=True)
class Master:
    name: str = attr.ib(default="")
    location: Dict[str, int] = attr.ib(default=attr.Factory(dict))

    alignmentZones: List[AlignmentZone] = attr.ib(default=attr.Factory(list))
    hStems: List[int] = attr.ib(default=attr.Factory(list))
    vStems: List[int] = attr.ib(default=attr.Factory(list))

    ascender: int = attr.ib(default=800)
    capHeight: int = attr.ib(default=700)
    descender: int = attr.ib(default=-200)
    italicAngle: float = attr.ib(default=0.)
    xHeight: int = attr.ib(default=500)

    _guidelines: List[Guideline] = attr.ib(default=attr.Factory(list))
    hKerning: Dict[str, Dict[str, int]] = attr.ib(default=attr.Factory(dict))
    vKerning: Dict[str, Dict[str, int]] = attr.ib(default=attr.Factory(dict))

    _parent: Optional[Any] = attr.ib(default=None, init=False)

    def __repr__(self):
        more = ""
        font = self._parent
        if font is not None:
            loc = self.location
            axes = font.axes
            for tag in ("wght", "wdth"):
                try:
                    more += ", %s=%r" % (tag, loc.get(tag, axes[tag]))
                except KeyError:
                    pass
        return "%s(%r%s)" % (self.__class__.__name__, self.name, more)

    @property
    def guidelines(self):
        return observable_list(self, self._guidelines)

    @property
    def parent(self):
        return self._parent


fontMasterList = lambda: [Master(name="Regular")]
