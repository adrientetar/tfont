import attr
from typing import Any, Dict, Optional

# add access to interpolated glyphs --> Instance.glyphs

# api to export font
# api to convert an instance into a master?


@attr.s(auto_attribs=True, cmp=False, repr=False, slots=True)
class Instance:
    familyName: str = ""
    styleName: str = ""
    location: Dict[str, int] = attr.Factory(dict)

    bold: bool = False
    italic: bool = False
    preferredFamilyName: str = ""
    preferredSubfamilyName: str = ""
    postscriptFontName: str = ""
    postscriptFullName: str = ""

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
        name = f"{self.familyName} {self.styleName}".rstrip()
        return "%s(%r%s)" % (self.__class__.__name__, name, more)

    @property
    def parent(self):
        return self._parent
