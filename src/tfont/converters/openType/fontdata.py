from fontTools.cffLib.width import optimizeWidths
from fontTools.misc.fixedTools import otRound
import math
from tfont.converters.openType import conversion, semlog
from tfont.objects import Glyph, Layer, Path, Point
from tfont.objects.misc import Rectangle


def rect_otRound(rectangle):
    return Rectangle.from_points(
        otRound(rectangle.left),
        otRound(rectangle.bottom),
        otRound(rectangle.right),
        otRound(rectangle.top)
    )


class Assert:

    @staticmethod
    def is_u16(ctx, value):
        pass


# should I normalize the glyph names to postscript as well?

# proposed rearch: make fontdata contain fontproc?
# or just make ctx contain the output of it

# run once the logging things https://stackoverflow.com/a/4104188

# => actually, a good way to avoid duplicate logging is to memoize the return values

class FontData:
    known_stylenames = {"regular", "bold", "italic", "bold italic"}

    @classmethod
    def copyright(cls, ctx):
        font = ctx.font

        return font.copyright

    @classmethod
    def date(cls, ctx):
        font = ctx.font

        return font.date

    @classmethod
    def designer(cls, ctx):
        font = ctx.font

        return font.designer

    @classmethod
    def designerURL(cls, ctx):
        font = ctx.font

        return font.designerURL

    @classmethod
    def manufacturer(cls, ctx):
        font = ctx.font

        return font.manufacturer

    @classmethod
    def manufacturerURL(cls, ctx):
        font = ctx.font

        return font.manufacturerURL

    @classmethod
    def unitsPerEm(cls, ctx):
        font = ctx.font

        return font.unitsPerEm

    @classmethod
    def version(cls, ctx):
        font = ctx.font

        versionMinor = str(font.versionMinor)
        # limit minor version to 3 digits as recommended in OpenType spec:
        # https://www.microsoft.com/typography/otspec/recom.htm
        actualVersionMinor = versionMinor.zfill(3)[:3]
        if len(versionMinor) > 3:
            ctx.log.append(
                semlog.warning_attr_truncated(attr="versionMinor", result=actualVersionMinor)
            )
        return f"{font.versionMajor}.{actualVersionMinor}"

    ##

    @classmethod
    def ascender(cls, ctx):
        master = ctx.master

        return master.ascender

    @classmethod
    def capHeight(cls, ctx):
        master = ctx.master

        return master.capHeight

    @classmethod
    def CFF_postscriptBlueFuzz(cls, ctx):
        return 0

    @classmethod
    def CFF_postscriptBlueScale(cls, ctx):
        blues = cls.CFF_postscriptBlueValues(ctx)
        otherBlues = cls.CFF_postscriptOtherBlues(ctx)
        maxZoneHeight = 0
        blueScale = 0.039625

        if blues:
            assert len(blues) % 2 == 0
            for x, y in zip(blues[:-1:2], blues[1::2]):
                maxZoneHeight = max(maxZoneHeight, abs(y - x))
        if otherBlues:
            assert len(otherBlues) % 2 == 0
            for x, y in zip(otherBlues[:-1:2], otherBlues[1::2]):
                maxZoneHeight = max(maxZoneHeight, abs(y - x))
        if maxZoneHeight != 0:
            blueScale = 3 / (4 * maxZoneHeight)
        return blueScale

    @classmethod
    def CFF_postscriptBlueShift(cls, ctx):
        return 7

    @classmethod
    def CFF_postscriptBlueValues(cls, ctx):
        master = ctx.master

        return list(cls._collect_blues(
            master.alignmentZones,
            lambda zone: zone.position >= 0
        ))

    @classmethod
    def CFF_postscriptFamilyBlues(cls, ctx):
        return []

    @classmethod
    def CFF_postscriptFamilyName(cls, ctx):
        preferredFamilyName = cls.name_preferredFamilyName(ctx)

        return preferredFamilyName

    @classmethod
    def CFF_postscriptFamilyOtherBlues(cls, ctx):
        return []

    @classmethod
    def CFF_postscriptForceBold(cls, ctx):
        return False

    @classmethod
    def CFF_postscriptOtherBlues(cls, ctx):
        master = ctx.master

        return list(cls._collect_blues(
            master.alignmentZones,
            lambda zone: zone.position < 0
        ))

    @classmethod
    def CFF_postscriptStemSnapH(cls, ctx):
        return []

    @classmethod
    def CFF_postscriptStemSnapV(cls, ctx):
        return []

    @classmethod
    def CFF_postscriptWeightName(cls, ctx):
        preferredSubfamilyName = cls.name_preferredSubfamilyName(ctx)

        return preferredSubfamilyName

    @classmethod
    def descender(cls, ctx):
        master = ctx.master

        return master.descender

    @classmethod
    def head_macStyle(cls, ctx):
        styleMapName = cls.stylemap_styleName(ctx)

        macStyle = 0
        if styleMapName.startswith("bold"):
            macStyle |= 1 << 0
        if styleMapName.endswith("italic"):
            macStyle |= 1 << 1
        return macStyle

    @classmethod
    def hhea_caretMetrics(cls, ctx):
        master = ctx.master
        italicAngle = master.italicAngle

        if italicAngle:
            caretSlopeRise = 1000
            caretSlopeRun = otRound(
                math.tan(math.radians(-italicAngle)) * caretSlopeRise)
        else:
            caretSlopeRise = 1
            caretSlopeRun = 0

        return (
            caretSlopeRise,
            caretSlopeRun,
            0
        )

    @classmethod
    def hhea_metrics(cls, ctx):
        return cls.OS2_typoMetrics(ctx)

    @classmethod
    def head_version(cls, ctx):
        version = cls.version(ctx)

        return float(version)

    @classmethod
    def italicAngle(cls, ctx):
        master = ctx.master

        return master.italicAngle

    @classmethod
    def name_description(cls, ctx):
        return None

    @classmethod
    def name_license(cls, ctx):
        return None

    @classmethod
    def name_licenseURL(cls, ctx):
        return None

    @classmethod
    def name_postscriptFontName(cls, ctx):
        preferredFamilyName = cls.name_preferredFamilyName(ctx)
        preferredSubfamilyName = cls.name_preferredSubfamilyName(ctx)

        return conversion.to_postscript_name(
            f"{preferredFamilyName}-{preferredSubfamilyName}")

    @classmethod
    def name_postscriptFullName(cls, ctx):
        preferredFamilyName = cls.name_preferredFamilyName(ctx)
        preferredSubfamilyName = cls.name_preferredSubfamilyName(ctx)

        return f"{preferredFamilyName} {preferredSubfamilyName}"

    @classmethod
    def name_uniqueID(cls, ctx):
        version = cls.name_version(ctx).replace("Version ", "")
        vendor = cls.OS2_vendorID(ctx)
        fontName = cls.name_postscriptFontName(ctx)
        return f"{version};{vendor};{fontName}"

    @classmethod
    def name_version(cls, ctx):
        version = cls.version(ctx)

        return f"Version {version}"

    @classmethod
    def name_preferredFamilyName(cls, ctx):
        #master = ctx.master  # XXX: PFN is in Instance
        font = ctx.font

        return font.familyName#master.familyName

    @classmethod
    def name_preferredSubfamilyName(cls, ctx):
        # XXX: PSN is in Instance
        master = ctx.master

        return master.name

    @classmethod
    def name_trademark(cls, ctx):
        return ""

    @classmethod
    def OS2_codepageRanges(cls, ctx):
        return None

    @classmethod
    def OS2_familyClass(cls, ctx):
        ibmFontClass = 0
        ibmFontSubclass = 0

        return (ibmFontClass << 8) + ibmFontSubclass

    @classmethod
    def OS2_fsSelection(cls, ctx):
        selection = 0
        styleMapStyleName = cls.stylemap_styleName(ctx)
        useTypoMetrics = cls.OS2_useTypoMetrics(ctx)

        if styleMapStyleName == "regular":
            selection |= 1 << 6
        else:
            if styleMapStyleName.startswith("bold"):
                selection |= 1 << 5
            if styleMapStyleName.endswith("italic"):
                selection |= 1 << 0
        if useTypoMetrics:
            selection |= 1 << 7

        return selection

    @classmethod
    def OS2_fsType(cls, ctx):
        # bit 2: Preview & Print embedding
        return 1 << 2

    @classmethod
    def OS2_panose(cls, ctx):
        return (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    @classmethod
    def OS2_strikeoutPosition(cls, ctx):
        xHeight = cls.xHeight(ctx)

        return xHeight * 0.6

    @classmethod
    def OS2_strikeoutSize(cls, ctx):
        underlineThickness = cls.post_underlineThickness(ctx)

        return underlineThickness

    @classmethod
    def OS2_subscriptXOffset(cls, ctx):
        italicAngle = cls.italicAngle(ctx)
        subscriptYOffset = cls.OS2_subscriptYOffset(ctx)

        return FontProc.adjust_offset(-subscriptYOffset, italicAngle)

    @classmethod
    def OS2_subscriptYOffset(cls, ctx):
        unitsPerEm = cls.unitsPerEm(ctx)

        return unitsPerEm * 0.075

    @classmethod
    def OS2_subscriptXSize(cls, ctx):
        unitsPerEm = cls.unitsPerEm(ctx)

        return unitsPerEm * 0.65

    @classmethod
    def OS2_subscriptYSize(cls, ctx):
        unitsPerEm = cls.unitsPerEm(ctx)

        return unitsPerEm * 0.6

    @classmethod
    def OS2_superscriptXOffset(cls, ctx):
        italicAngle = cls.italicAngle(ctx)
        superscriptYOffset = cls.OS2_superscriptYOffset(ctx)

        return FontProc.adjust_offset(superscriptYOffset, italicAngle)

    @classmethod
    def OS2_superscriptYOffset(cls, ctx):
        unitsPerEm = cls.unitsPerEm(ctx)

        return unitsPerEm * 0.35

    @classmethod
    def OS2_superscriptXSize(cls, ctx):
        return cls.OS2_subscriptXSize(ctx)

    @classmethod
    def OS2_superscriptYSize(cls, ctx):
        return cls.OS2_subscriptYSize(ctx)

    @classmethod
    def OS2_typoMetrics(cls, ctx):
        ascender = cls.ascender(ctx)
        descender = cls.descender(ctx)
        unitsPerEm = cls.unitsPerEm(ctx)

        return (
            ascender,
            descender,
            max(int(unitsPerEm * 1.2) - ascender + descender, 0)
        )

    @classmethod
    def OS2_unicodeRanges(cls, ctx):
        return None

    # part of OS2_fsSelection
    @classmethod
    def OS2_useTypoMetrics(cls, ctx):
        return True

    @classmethod
    def OS2_vendorID(cls, ctx):
        return "UKWN"

    @classmethod
    def OS2_weightClass(cls, ctx):
        return 400

    @classmethod
    def OS2_winMetrics(cls, ctx, font_bounds):
        typoAscender, \
        typoDescender, \
        typoLineGap = cls.OS2_typoMetrics(ctx)

        return (
            max(typoAscender, font_bounds.top),
            abs(min(typoDescender, font_bounds.bottom))
        )

    @classmethod
    def OS2_widthClass(cls, ctx):
        return 5

    @classmethod
    def post_isFixedPitch(cls, ctx):
        return False

    @classmethod
    def post_underlinePosition(cls, ctx):
        unitsPerEm = cls.unitsPerEm(ctx)

        return unitsPerEm * -0.075

    @classmethod
    def post_underlineThickness(cls, ctx):
        unitsPerEm = cls.unitsPerEm(ctx)

        return unitsPerEm * 0.05

    # stylemap?
    @classmethod
    def stylemap_familyName(cls, ctx):
        font = ctx.font

        return font.familyName

    @classmethod
    def stylemap_styleName(cls, ctx):
        master = ctx.master
        styleName = master.name.lower()

        if styleName in cls.known_stylenames:
            return styleName
        return "regular"

    @classmethod
    def xHeight(cls, ctx):
        master = ctx.master

        return master.xHeight

    ##

    @classmethod
    def glyph_layer(cls, ctx, glyph):
        master = ctx.master

        return glyph.layerForMaster(master)

    @classmethod
    def glyph_width(cls, ctx, glyph):
        layer = cls.glyph_layer(ctx, glyph)

        return cls.layer_width(ctx, layer)

    @classmethod
    def layer_width(cls, ctx, layer):
        width = layer.width

        if width < 0:
            ctx.log.append(
                semlog.error_negative_width(name=glyph.name, width=width)
            )
            return 0
        return width

    ##

    @staticmethod
    def _collect_blues(zones, condition):
        for zone in zones:
            if condition(zone):
                yield zone.position
                yield zone.position + zone.size


class FontProc:

    @staticmethod
    def average_char_width(ctx, otf):
        hmtx = otf.get("hmtx")

        if hmtx is not None:
            widths = list(filter(
                lambda w: w > 0,
                map(lambda hrec: hrec[0], hmtx.metrics.values())
            ))
            if widths:
                return otRound(sum(widths) / len(widths))
        else:
            ctx.log.append(
                semlog.warning_missing_hmtx(target="avgCharWidth")
            )
        return 0

    @staticmethod
    def codepage_ranges(ctx, unicodes):
        codepageRanges = set()

        chars = [chr(u) for u in unicodes]

        hasAscii = set(range(0x20, 0x7E)).issubset(unicodes)
        hasLineart = "┤" in chars

        for char in chars:
            if char == "Þ" and hasAscii:
                codepageRanges.add(0)  # Latin 1
            elif char == "Ľ" and hasAscii:
                codepageRanges.add(1)  # Latin 2: Eastern Europe
                if hasLineart:
                    codepageRanges.add(58)  # Latin 2
            elif char == "Б":
                codepageRanges.add(2)  # Cyrillic
                if "Ѕ" in chars and hasLineart:
                    codepageRanges.add(57)  # IBM Cyrillic
                if "╜" in chars and hasLineart:
                    codepageRanges.add(49)  # MS-DOS Russian
            elif char == "Ά":
                codepageRanges.add(3)  # Greek
                if hasLineart and "½" in chars:
                    codepageRanges.add(48)  # IBM Greek
                if hasLineart and "√" in chars:
                    codepageRanges.add(60)  # Greek, former 437 G
            elif char == "İ" and hasAscii:
                codepageRanges.add(4)  # Turkish
                if hasLineart:
                    codepageRanges.add(56)  # IBM turkish
            elif char == "א":
                codepageRanges.add(5)  # Hebrew
                if hasLineart and "√" in chars:
                    codepageRanges.add(53)  # Hebrew
            elif char == "ر":
                codepageRanges.add(6)  # Arabic
                if "√" in chars:
                    codepageRanges.add(51)  # Arabic
                if hasLineart:
                    codepageRanges.add(61)  # Arabic; ASMO 708
            elif char == "ŗ" and hasAscii:
                codepageRanges.add(7)  # Windows Baltic
                if hasLineart:
                    codepageRanges.add(59)  # MS-DOS Baltic
            elif char == "₫" and hasAscii:
                codepageRanges.add(8)  # Vietnamese
            elif char == "ๅ":
                codepageRanges.add(16)  # Thai
            elif char == "エ":
                codepageRanges.add(17)  # JIS/Japan
            elif char == "ㄅ":
                codepageRanges.add(18)  # Chinese: Simplified chars
            elif char == "ㄱ":
                codepageRanges.add(19)  # Korean wansung
            elif char == "央":
                codepageRanges.add(20)  # Chinese: Traditional chars
            elif char == "곴":
                codepageRanges.add(21)  # Korean Johab
            elif char == "♥" and hasAscii:
                codepageRanges.add(30)  # OEM Character Set
            # TODO: Symbol bit has a special meaning (check the spec), we need
            # to confirm if this is wanted by default.
            # elif chr(0xF000) <= char <= chr(0xF0FF):
            #    codepageRanges.add(31)          # Symbol Character Set
            elif char == "þ" and hasAscii and hasLineart:
                codepageRanges.add(54)  # MS-DOS Icelandic
            elif char == "╚" and hasAscii:
                codepageRanges.add(62)  # WE/Latin 1
                codepageRanges.add(63)  # US
            elif hasAscii and hasLineart and "√" in chars:
                if char == "Å":
                    codepageRanges.add(50)  # MS-DOS Nordic
                elif char == "é":
                    codepageRanges.add(52)  # MS-DOS Canadian French
                elif char == "õ":
                    codepageRanges.add(55)  # MS-DOS Portuguese

        if hasAscii and "‰" in chars and "∑" in chars:
            codepageRanges.add(29)  # Macintosh Character Set (US Roman)

        # when no codepage ranges can be enabled, fall back to enabling bit 0
        # (Latin 1) so that the font works in MS Word:
        # https://github.com/googlei18n/fontmake/issues/468
        if not codepageRanges:
            codepageRanges.add(0)

        return codepageRanges

    @staticmethod
    def font_glyph_bounds(ctx, glyphMap):
        glyphBoundsMap = {}

        fontBounds = Rectangle.create_empty()
        for glyphName, glyph in glyphMap.items():
            rectangle = Rectangle.create_empty()
            for path in glyph.layers[0].paths:
                for point in path.points:
                    rectangle.unionPt(point.x, point.y)
            if not rectangle.empty:
                rectangle = rect_otRound(rectangle)
            glyphBoundsMap[glyphName] = rectangle
            fontBounds.union(rectangle)
        return fontBounds, glyphBoundsMap

    @staticmethod
    def minmax_cids(ctx, unicodes):
        if unicodes:
            minIndex = min(unicodes)
            maxIndex = max(unicodes)
        else:
            # the font may have *no* unicode values (it really happens!) so
            # there needs to be a fallback. use 0xFFFF, as AFDKO does:
            # FDK/Tools/Programs/makeotf/makeotf_lib/source/hotconv/map.c
            minIndex = 0xFFFF
            maxIndex = 0xFFFF
        if maxIndex > 0xFFFF:
            # the spec says that 0xFFFF should be used
            # as the max if the max exceeds 0xFFFF
            maxIndex = 0xFFFF
        return minIndex, maxIndex

    @staticmethod
    def postscript_width_stats(ctx, otf):
        hmtx = otf.get("hmtx")

        if hmtx is not None:
            widths = [m[0] for m in hmtx.metrics.values()]
            return optimizeWidths(widths)
        else:
            ctx.log.append(
                semlog.warning_missing_hmtx(target="defaultWidthX/nominalWidthX")
            )
        return 0, 0

    @staticmethod
    def production_glyphs(ctx):
        font = ctx.font

        glyphs = {glyph.name: glyph for glyph in font.glyphs}
        if len(glyphs) < len(font.glyphs):
            duplicates = []
            glyphNames = set()

            for glyph in font.glyphs:
                if glyph.name in glyphNames:
                    duplicates.append(glyph.name)
                glyphNames.add(glyph.name)
            assert len(duplicates)
            ctx.log.append(
                semlog.error_duplicate_glyphs(duplicates=duplicates)
            )
        if ".notdef" not in glyphs:
            glyphs[".notdef"] = FontProc.make_notdef(ctx)

        order = [".notdef"]
        order.extend(
            filter(lambda glyphName: glyphName != ".notdef", glyphs.keys())
        )
        return glyphs, order

    @staticmethod
    def unicode_glyphname_map(ctx, glyphMap):
        cmap = {}
        for glyphName, glyph in glyphMap.items():
            unicodes = glyph.unicodes
            for cp in map(conversion.to_codepoint, unicodes):
                if cp in cmap:
                    ctx.log.append(
                        semlog.error_duplicate_encoding(
                            name=glyphName,
                            unicode=conversion.from_codepoint(cp),
                            oldName=cmap[cp],
                        )
                    )
                cmap[cp] = glyphName
        return cmap


    ##

    @staticmethod
    def adjust_offset(offset, angle):
        """Adjust Y offset based on italic angle, to get X offset."""
        return offset * math.tan(math.radians(-angle)) if angle else 0

    @staticmethod
    def is_non_bmp(string):
        return any(ord(c) > 65535 for c in string)


    ##

    @staticmethod
    def make_notdef(ctx):
        font = ctx.font
        upm = FontData.unitsPerEm(ctx)
        width = otRound(.5 * upm)
        margin = otRound(.05 * upm)
        stroke = otRound(.03 * upm)
        ascender = otRound(FontData.ascender(ctx))
        paths = []

        xMin = margin
        xMax = width - margin
        yMax = ascender
        yMin = 0
        paths.append(
            Path(points=[
                Point(xMin, yMin, "line"),
                Point(xMax, yMin, "line"),
                Point(xMax, yMax, "line"),
                Point(xMin, yMax, "line"),
            ]))
        xMin += stroke
        xMax -= stroke
        yMax -= stroke
        yMin += stroke
        paths.append(
            Path(points=[
                Point(xMin, yMin, "line"),
                Point(xMin, yMax, "line"),
                Point(xMax, yMax, "line"),
                Point(xMax, yMin, "line"),
            ]))

        return Glyph(".notdef", layers=[
            Layer(masterName=ctx.master.name, paths=paths)
        ])