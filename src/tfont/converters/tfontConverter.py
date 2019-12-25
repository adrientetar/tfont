import cattr
from collections.abc import Collection
from datetime import datetime
import rapidjson as json
from rapidjson import RawJSON
from tfont.objects.font import Font
from tfont.objects.layer import Layer
from tfont.objects.misc import AlignmentZone, Matrix3x2
from tfont.objects.path import Path
from tfont.objects.point import Point
from typing import Union


def _structure_Path(data, cls):
    points = []
    extraData = None
    if data[-1].__class__ is dict:
        extraData = data[-1]
        data = data[:-1]
    for arr in data:
        if arr[-1].__class__ is dict:
            _extraData = arr[-1]
            point = Point(*arr[:-1])
            point._extraData = _extraData
        else:
            point = Point(*arr)
        points.append(point)
    path = cls(points)
    if extraData is not None:
        path._extraData = extraData
    return path


def _unstructure_Path(path):
    data = []
    for point in path._points:
        ptType = point.type
        if ptType is not None:
            if point.smooth:
                value = (point.x, point.y, ptType, True)
            else:
                value = (point.x, point.y, ptType)
        else:
            value = (point.x, point.y)
        extraData = point._extraData
        if extraData:
            value += (extraData,)
        data.append(RawJSON(json.dumps(value)))
    if path._extraData:
        data.append(path._extraData)
    return data


def _unstructure_Path_base(path):
    data = []
    for point in path._points:
        ptType = point.type
        if ptType is not None:
            if point.smooth:
                value = (point.x, point.y, ptType, True)
            else:
                value = (point.x, point.y, ptType)
        else:
            value = (point.x, point.y)
        extraData = point._extraData
        if extraData:
            value += (extraData,)
        data.append(value)
    if path._extraData:
        data.append(path._extraData)
    return data


class TFontConverter(cattr.Converter):
    __slots__ = "_font", "_indent"

    version = 0

    def __init__(self, indent=0, **kwargs):
        super().__init__(**kwargs)
        self._indent = indent

        # datetime
        dateFormat = '%Y-%m-%d %H:%M:%S'
        self.register_structure_hook(
            datetime, lambda d, _: datetime.strptime(d, dateFormat))
        self.register_unstructure_hook(
            datetime, lambda dt: dt.strftime(dateFormat))
        # Number disambiguation (json gave the right type already)
        self.register_structure_hook(Union[int, float], lambda d, _: d)

        structure_seq = lambda d, t: t(*d)
        if indent is None:
            unstructure_seq = lambda o: tuple(o)
        else:
            unstructure_seq = lambda o: RawJSON(json.dumps(tuple(o)))
            self.register_unstructure_hook(tuple, unstructure_seq)
        # Alignment zone
        self.register_structure_hook(AlignmentZone, structure_seq)
        self.register_unstructure_hook(AlignmentZone, unstructure_seq)
        # Matrix3x2
        self.register_structure_hook(Matrix3x2, structure_seq)
        self.register_unstructure_hook(Matrix3x2, unstructure_seq)
        # Path
        self.register_structure_hook(Path, _structure_Path)
        if indent is None:
            self.register_unstructure_hook(Path, _unstructure_Path_base)
        else:
            self.register_unstructure_hook(Path, _unstructure_Path)


    def open(self, path, font=None):
        with open(path, 'r') as file:
            d = json.load(file)
        # XXX: default to 0 for now because Fonte doesn't add this attr
        assert self.version >= d.pop(".formatVersion", 0)
        if font is not None:
            self._font = font
        return self.structure(d, Font)

    def save(self, font, path):
        d = self.unstructure(font)
        with open(path, 'w') as file:
            json.dump(d, file, indent=self._indent)
        return True, []

    def structure_attrs_fromdict(self, obj, cl):
        conv_obj = obj.copy()  # Dict of converted parameters.
        dispatch = self._structure_func.dispatch
        for a in cl.__attrs_attrs__:
            # We detect the type by metadata.
            type_ = a.type
            if type_ is None:
                # No type.
                continue
            name = a.name
            if name[0] == "_":
                name = name[1:]
            try:
                val = obj[name]
            except KeyError:
                continue
            conv_obj[name] = dispatch(type_)(val, type_)

        if cl is Font:
            try:
                font = self._font
                font.__init__(**conv_obj)
                del self._font
                return font
            except:
                pass
        return cl(**conv_obj)

    def unstructure_attrs_asdict(self, obj):
        cls = obj.__class__
        attrs = cls.__attrs_attrs__
        dispatch = self._unstructure_func.dispatch
        # add version stamp
        if cls is Font:
            rv = {".formatVersion": self.version}
        else:
            rv = {}
        for a in attrs:
            # skip internal attrs
            if not a.init:
                continue
            name = a.name
            v = getattr(obj, name)
            if not v:
                # skip attrs that have trivial default values set
                if v == a.default:
                    continue
                # skip empty collections
                if isinstance(v, Collection):
                    continue
            # remove underscore from private attrs
            if name[0] == "_":
                name = name[1:]
            rv[name] = dispatch(v.__class__)(v)
        return rv
