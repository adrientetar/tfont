import attr
from tfont.objects.guideline import Guideline
from tfont.objects.misc import AlignmentZone, observable_list
from typing import Any, Dict, List, Optional


@attr.s(auto_attribs=True, cmp=False, repr=False, slots=True)
class Master:
    name: str
    location: Dict[str, int] = attr.Factory(dict)

    alignmentZones: List[AlignmentZone] = attr.Factory(list)
    hStems: List[int] = attr.Factory(list)
    vStems: List[int] = attr.Factory(list)

    ascender: int = 800
    capHeight: int = 700
    descender: int = -200
    italicAngle: float = 0.
    xHeight: int = 500

    _guidelines: List[Guideline] = attr.Factory(list)
    hKerning: Dict[str, Dict[str, int]] = attr.Factory(dict)
    vKerning: Dict[str, Dict[str, int]] = attr.Factory(dict)

    _parent: Optional[Any] = attr.ib(default=None, init=False)

    def __repr__(self):
        more = ""
        font = self._parent
        if font is not None:
            loc = self.location
            for tag in ("wght", "wdth"):
                axis = font.axisForTag(tag)
                more += ", %s=%r" % (tag, loc.get(tag, axis))
        return "%s(%r%s)" % (self.__class__.__name__, self.name, more)

    @property
    def guidelines(self):
        return observable_list(self, self._guidelines)

    @property
    def parent(self):
        return self._parent


fontMasterList = lambda: [Master(name="Regular")]
