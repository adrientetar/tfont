import cattr
from datetime import datetime
from tfont.objects.anchor import Anchor
from tfont.objects.component import Component
from tfont.objects.font import Font
from tfont.objects.glyph import Glyph
from tfont.objects.layer import Layer
from tfont.objects.guideline import Guideline
from tfont.objects.misc import AlignmentZone, Matrix3x2
from tfont.objects.path import Path
from typing import Union

try:
    import ufoLib2
except ImportError:
    ufoLib2 = None


class UFOConverter(cattr.Converter):
    __slots__ = ()

    def __init__(self, **kwargs):
        if ufoLib2 is None:
            raise ImportError(
                "No module named 'ufoLib2'. This is required to use the "
                "UFOConverter. Please re-install tfont with 'ufo' extra:\n"
                "    $ pip install tfont[ufo]"
            )

        super().__init__(**kwargs)
        self.register_structure_hook(Union[int, float], lambda d, _: d)

    def open(self, path, font=None):
        if font is None:
            font = Font()
        ufo = ufoLib2.Font.open(path)
        # font
        info = ufo.info
        if info.openTypeHeadCreated:
            try:
                font.date = datetime.strptime(
                    info.openTypeHeadCreated, "%Y/%m/%d %H:%M:%S"
                )
            except ValueError:
                pass
        if info.familyName:
            font.familyName = info.familyName
        if info.copyright:
            font.copyright = info.copyright
        if info.openTypeNameDesigner:
            font.designer = info.openTypeNameDesigner
        if info.openTypeNameDesignerURL:
            font.designerURL = info.openTypeNameDesignerURL
        if info.openTypeNameManufacturer:
            font.manufacturer = info.openTypeNameManufacturer
        if info.openTypeNameManufacturerURL:
            font.manufacturerURL = info.openTypeNameManufacturerURL
        if info.unitsPerEm:
            font.unitsPerEm = info.unitsPerEm
        if info.versionMajor:
            font.versionMajor = info.versionMajor
        if info.versionMinor:
            font.versionMinor = info.versionMinor
        if ufo.lib:
            font._extraData = ufo.lib
        # master
        master = font.selectedMaster
        if info.styleName:
            master.name = info.styleName
        for blues in (info.postscriptBlueValues, info.postscriptOtherBlues):
            for yMin, yMax in zip(blues[::2], blues[1::2]):
                master.alignmentZones.append(AlignmentZone(yMin, yMax - yMin))
        if info.postscriptStemSnapH:
            master.hStems = info.postscriptStemSnapH
        if info.postscriptStemSnapV:
            master.vStems = info.postscriptStemSnapV
        if ufo.guidelines:
            for g in ufo.guidelines:
                guideline = Guideline(
                    x=g.x or 0, y=g.y or 0, angle=g.angle or 0, name=g.name or ""
                )
                # ufo guideline color and identifier are skipped
                master.guidelines.append(guideline)
        # note: unlike ufo, we store kerning in visual order. hard to convert
        # between the two (given that ltr and rtl pairs can be mixed)
        if ufo.kerning:
            hKerning = {}
            for (first, second), value in ufo.kerning.items():
                if first not in hKerning:
                    hKerning[first] = {}
                hKerning[first][second] = value
            master.hKerning = hKerning
        if info.ascender:
            master.ascender = info.ascender
        if info.capHeight:
            master.capHeight = info.capHeight
        if info.descender:
            master.descender = info.descender
        if info.italicAngle:
            master.italicAngle = info.italicAngle
        if info.xHeight:
            master.xHeight = info.xHeight
        # glyphs
        font._glyphs.clear()
        glyphs = font.glyphs
        for glyph_name in ufo_glyph_order(ufo):
            glyph = Glyph(glyph_name)
            glyphs.append(glyph)
            # TODO assign kerning groups

            for ufo_layer in ufo.layers:
                # Layer.
                if glyph_name not in ufo_layer:
                    continue

                # We only need one layer for the master as UFOs are single
                # masters. Different layers from the UFO are appended under the
                # same master layer with a "name" attribute.
                g = ufo_layer[glyph_name]
                if ufo_layer.name == "public.default":
                    layer = glyph.layerForMaster(None)
                else:
                    master_layer = glyph.layerForMaster(None)
                    layer = Layer(
                        masterName=master_layer.masterName, name=ufo_layer.name
                    )
                    glyph.layers.append(layer)

                # Use first Unicode value we find, unless already set.
                if g.unicodes and not glyph.unicodes:
                    glyph.unicodes = [f"{uv:04X}" for uv in g.unicodes]

                layer.width = g.width
                layer.height = g.height
                lib = g.lib
                vertOrigin = lib.pop("public.verticalOrigin", None)
                if vertOrigin:
                    layer.yOrigin = vertOrigin
                color = lib.pop("public.markColor", None)
                if color:
                    glyph.color = tuple(
                        round(float(component) * 255) for component in color.split(",")
                    )
                if lib:
                    layer._extraData = lib

                # anchors
                anchors = layer.anchors
                for a in g.anchors:
                    if not a.name:
                        continue
                    anchors.append(Anchor(a.x or 0, a.y or 0, a.name))
                    # ufo color and identifier are skipped
                # components
                components = layer.components
                for c in g.components:
                    component = Component(c.baseGlyph)
                    if c.transformation:
                        component.transformation = Matrix3x2(
                            *tuple(c.transformation)
                        )
                    # ufo identifier is skipped
                    components.append(component)
                # guidelines
                guidelines = layer.guidelines
                for g_ in g.guidelines:
                    guideline = Guideline(g_.x or 0, g_.y or 0, g_.angle or 0)
                    if g_.name:
                        guideline.name = g_.name
                    # ufo color and identifier are skipped
                    guidelines.append(guideline)
                # paths
                paths = layer.paths
                for c in self.unstructure(g.contours):
                    pts = c.pop("points")
                    for p in pts:
                        name = p.pop("name", None)
                        ident = p.pop("identifier", None)
                        if name or ident:
                            p["extraData"] = d = {}
                            if name:
                                d["name"] = name
                            if ident:
                                d["id"] = ident
                    while pts[-1]["type"] is None:
                        pts.insert(0, pts.pop())
                    c["points"] = pts
                    ident = c.pop("identifier", None)
                    if ident:
                        c["id"] = ident
                    path = self.structure(c, Path)
                    paths.append(path)
        return font

    def save(self, font, path):
        raise NotImplementedError

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

        return cl(**conv_obj)


def ufo_glyph_order(ufo_font):
    glyph_order = ufo_font.glyphOrder
    if glyph_order:
        glyph_order_set = set(glyph_order)

        ufo_glyph_names = {glyph.name for glyph in ufo_font}
        if ufo_glyph_names.issubset(glyph_order_set):
            return glyph_order

        glyph_order_missing = ufo_glyph_names - glyph_order_set
        glyph_order.extend(glyph_order_missing)
        return glyph_order

    return [glyph.name for glyph in ufo_font]
