import attr
from datetime import datetime
from tfont.objects.axis import Axis
from tfont.objects.glyph import Glyph
from tfont.objects.instance import Instance
from tfont.objects.master import Master, fontMasterList
from tfont.objects.misc import observable_list
from typing import Dict, List, Optional


@attr.s(auto_attribs=True, cmp=False, repr=False, slots=True)
class Font:
    date: datetime = attr.Factory(datetime.utcnow)
    familyName: str = "New Font"

    _axes: List[Axis] = attr.Factory(list)
    _glyphs: List[Glyph] = attr.Factory(list)
    _masters: List[Master] = attr.Factory(fontMasterList)
    _instances: List[Instance] = attr.Factory(list)

    copyright: str = ""
    designer: str = ""
    designerURL: str = ""
    manufacturer: str = ""
    manufacturerURL: str = ""
    unitsPerEm: int = 1000
    versionMajor: int = 1
    versionMinor: int = 0

    _extraData: Optional[Dict] = None

    _selectedMaster: Optional[int] = attr.ib(default=None, init=False)

    def __attrs_post_init__(self):
        for axis in self._axes:
            axis._parent = self
        for glyph in self._glyphs:
            glyph._parent = self
        for master in self._masters:
            master._parent = self
        for instance in self._instances:
            instance._parent = self

    def __repr__(self):
        return "%s(%r, v%d.%d with %d masters and %d instances)" % (
            self.__class__.__name__, self.familyName, self.versionMajor,
            self.versionMinor, len(self._masters), len(self._instances))

    @property
    def axes(self):
        return observable_list(self, self._axes)

    @property
    def extraData(self):
        extraData = self._extraData
        if extraData is None:
            extraData = self._extraData = {}
        return extraData

    @property
    def glyphs(self):
        return observable_list(self, self._glyphs)

    @property
    def instances(self):
        return observable_list(self, self._instances)

    @property
    def layoutEngine(self):
        layoutEngine = self._layoutEngine
        if layoutEngine is None:
            layoutEngine = self._layoutEngine = self.layoutEngineFactory()
        return layoutEngine

    @property
    def masters(self):
        return observable_list(self, self._masters)

    @property
    def selectedMaster(self):
        try:
            return self._masters[self._selectedMaster]
        except (KeyError, TypeError):
            self._selectedMaster = 0
            return self._masters[0]

    def axisForTag(self, tag):
        for axis in self._axes:
            if axis.name == tag:
                return axis

    def glyphForName(self, name):
        for glyph in self._glyphs:
            if glyph.name == name:
                return glyph

    def glyphForUnicode(self, value):
        gid = self.glyphIdForCodepoint(int(value, 16))
        if gid is not None:
            return self._glyphs[gid]

    def glyphIdForCodepoint(self, value, default=None):
        for index, glyph in enumerate(self._glyphs):
            uni = glyph.unicode
            if uni is not None:
                ch = int(uni, 16)
                if ch == value:
                    return index
        return default

    # maybe we could only have glyphForName and inline this func
    def glyphIdForName(self, name):
        for index, glyph in enumerate(self._glyphs):
            if glyph.name == name:
                return index

    def masterForName(self, name):
        for master in self._masters:
            if master.name == name:
                return master
